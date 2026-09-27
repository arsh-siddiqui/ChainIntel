"""Investigation report service: JSON payload assembly, PDF and CSV rendering."""
from __future__ import annotations

import io
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Report
from app.services.serializers import case_event_dict, evidence_dict, threat_dict, tx_dict
from app.utils.datetime import iso, utcnow

REPORT_DISCLAIMERS = [
    "Analytical output should be independently validated before use in legal, regulatory, or operational decisions.",
    "Risk score is an analytical indicator and not a determination of unlawful activity.",
    "All blockchain data is retrieved from third-party providers and should be cross-verified against a full node or secondary explorer for evidentiary use.",
]


def collect_payload(db: Session, wallet_address: str, case_id: int | None = None) -> dict[str, Any]:
    """Assemble the report payload. Reuses the latest investigation if present."""
    from app.models import Case, CaseEvent, Evidence, Investigation, OSINTFinding, ThreatFinding, Transaction, Wallet
    from app.services.graph_analysis import build_graph, trace_funds
    from app.services.osint import correlate_wallet
    from app.services.risk_engine import assess as assess_risk
    from app.services.serializers import investigation_summary

    wallet = db.query(Wallet).filter(Wallet.address == wallet_address).one_or_none()
    tx_rows = (
        db.query(Transaction)
        .filter((Transaction.from_address == wallet_address) | (Transaction.to_address == wallet_address))
        .order_by(Transaction.timestamp.desc())
        .limit(100)
        .all()
    )
    txs = [tx_dict(t) for t in tx_rows]
    threat_rows = db.query(ThreatFinding).filter(ThreatFinding.wallet_address == wallet_address).all()
    threats = [threat_dict(t) for t in threat_rows]
    graph = build_graph(db, wallet_address, hops=2, max_nodes=100)
    fund_flow = trace_funds(db, wallet_address, direction="outgoing", max_hops=3)
    investigation = (
        db.query(Investigation)
        .filter(Investigation.wallet_address == wallet_address)
        .order_by(Investigation.created_at.desc())
        .first()
    )
    osint_results = correlate_wallet(wallet_address)

    if investigation and investigation.payload and investigation.payload.get("risk"):
        risk = investigation.payload["risk"]
    else:
        risk = assess_risk(
            {
                "focus_address": wallet_address,
                "transactions": txs,
                "threat_findings": threats,
                "counterparty_threats": [],
                "graph_stats": graph.get("stats", {}),
                "osint_findings": osint_results.get("results", []),
            }
        )

    case = db.query(Case).filter(Case.id == case_id).one_or_none() if case_id else None
    timeline = (
        [case_event_dict(e) for e in db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at.asc()).all()]
        if case
        else []
    )
    evidence_rows = db.query(Evidence).filter(Evidence.case_id == case.id).all() if case else []

    if investigation and investigation.payload and investigation.payload.get("wallet"):
        wallet_summary = investigation.payload["wallet"]
    else:
        wallet_summary = {
            "address": wallet_address,
            "blockchain": wallet.blockchain if wallet else "unknown",
            "balance": wallet.balance if wallet else 0.0,
            "asset": wallet.asset if wallet else "BTC",
            "transaction_count": wallet.transaction_count if wallet else len(txs),
            "is_demo": wallet.is_demo if wallet else False,
        }

    return {
        "report_id": uuid.uuid4().hex,
        "generated_at": iso(utcnow()),
        "mode": "LIVE",
        "app_version": settings.app_version,
        "case": {"id": case.id, "case_number": case.case_number, "title": case.title, "status": case.status, "priority": case.priority} if case else None,
        "wallet": wallet_address,
        "blockchain": wallet_summary.get("blockchain") or (wallet.blockchain if wallet else "unknown"),
        "wallet_summary": wallet_summary,
        "transactions": txs[:100],
        "threat_findings": threats,
        "osint_findings": [r for r in osint_results.get("results", []) if r["status"] in ("FOUND", "NOT_FOUND")],
        "risk_indicators": risk.get("indicators", []),
        "risk": risk,
        "fund_flow": {k: fund_flow.get(k) for k in ("path", "path_edges", "hops", "total_amount", "suspicious_nodes", "disclaimer", "levels") if k in fund_flow},
        "evidence": [evidence_dict(e) for e in evidence_rows],
        "timeline": timeline,
        "investigation": investigation_summary(investigation) if investigation else None,
        "status": case.status if case else (investigation.status if investigation else "Under Investigation"),
        "analyst_notes": investigation.notes if investigation else None,
        "disclaimers": REPORT_DISCLAIMERS,
    }


def create_report(db: Session, wallet_address: str, case_id: int | None, title: str | None) -> Report:
    from app.models import Report

    payload = collect_payload(db, wallet_address, case_id)
    report = Report(
        id=payload["report_id"],
        case_id=case_id,
        wallet_address=wallet_address,
        blockchain=payload.get("blockchain", "unknown"),
        title=title or f"Blockchain OSINT Investigation Report - {wallet_address[:20]}",
        mode=payload.get("mode", settings.app_mode.upper()),
        payload=payload,
    )
    db.add(report)
    db.commit()
    from app.services.audit import log_action

    log_action(db, "report_generated", "report", report.id, {"wallet_address": wallet_address, "case_id": case_id})
    return report


def get_report(db: Session, report_id: str) -> Report | None:
    from app.models import Report

    return db.query(Report).filter(Report.id == report_id).one_or_none()


def list_reports(db: Session, page: int = 1, page_size: int = 20):
    from app.models import Report
    from app.services.serializers import report_dict
    from app.utils.pagination import clamp, meta

    page, page_size = clamp(page, page_size)
    query = db.query(Report)
    total = query.count()
    items = query.order_by(Report.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [report_dict(r) for r in items], meta(page, page_size, total)


# ------------------------------------------------------------------ PDF
def render_pdf(payload: dict[str, Any]) -> bytes:
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    navy = colors.HexColor("#0F172A")
    primary = colors.HexColor("#2563EB")
    light = colors.HexColor("#F1F5F9")
    border = colors.HexColor("#CBD5E1")

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=22, textColor=navy, spaceAfter=4)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=navy, spaceBefore=14, spaceAfter=6)
    sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#475569"), alignment=TA_CENTER)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=13)
    note = ParagraphStyle("Note", parent=body, textColor=colors.HexColor("#B45309"))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    story: list = []

    def section(title: str) -> None:
        story.append(Paragraph(title, h2))
        story.append(HRFlowable(width="100%", color=border, thickness=0.5))

    def table(headers: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
        data = [headers] + rows
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), light),
                    ("TEXTCOLOR", (0, 0), (-1, 0), navy),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, border),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ]
            )
        )
        story.append(t)

    # Cover
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("ChainIntel", h1))
    story.append(Paragraph("Blockchain OSINT Investigation Report", sub))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="60%", color=primary, thickness=1.2))
    story.append(Spacer(1, 12))
    payload_case = payload.get("case") or {}
    meta_rows = [
        ["Case", payload_case.get("case_number", "N/A") if payload_case else "N/A"],
        ["Wallet", payload.get("wallet", "")],
        ["Blockchain", payload.get("blockchain", "")],
        ["Mode", str(payload.get("mode", "LIVE"))],
        ["Generated", payload.get("generated_at", "")],
        ["Report ID", payload.get("report_id", "")],
    ]
    table(["Field", "Value"], meta_rows, [40 * mm, 110 * mm])
    story.append(Spacer(1, 10))
    for disclaimer in REPORT_DISCLAIMERS:
        story.append(Paragraph(f"IMPORTANT: {disclaimer}", note))
    story.append(PageBreak())

    wallet = payload.get("wallet_summary") or {}
    story.append(Paragraph("1. Executive Summary", h2))
    risk = payload.get("risk") or {}
    exec_rows = [
        ["Wallet", wallet.get("address", payload.get("wallet", ""))],
        ["Blockchain", payload.get("blockchain", "")],
        ["Balance", f"{wallet.get('balance', 0)} {wallet.get('asset', '')}"],
        ["Transactions (observed)", wallet.get("transaction_count", len(payload.get("transactions", [])))],
        ["Threat findings", str(len(payload.get("threat_findings", [])))],
        ["OSINT findings (FOUND)", str(sum(1 for o in payload.get("osint_findings", []) if o.get("status") == "FOUND"))],
        ["Risk score / band", f"{risk.get('score', 0)} / {risk.get('band', 'N/A')}"],
        ["Investigation status", payload.get("status", "")],
    ]
    table(["Metric", "Value"], exec_rows, [50 * mm, 120 * mm])

    section("2. Wallet Information")
    table(
        ["Field", "Value"],
        [[k.replace("_", " ").title(), str(v)] for k, v in wallet.items() if v is not None][:14],
        [50 * mm, 120 * mm],
    )

    section("3. Transaction Summary")
    txs = payload.get("transactions", [])[:30]
    if txs:
        table(
            ["TX Hash", "From", "To", "Amount", "Timestamp"],
            [
                [t.get("tx_hash", "")[:26], str(t.get("from_address", ""))[:22], str(t.get("to_address", ""))[:22], f"{t.get('amount', 0)} {t.get('asset', '')}", str(t.get("timestamp", ""))[:19]]
                for t in txs
            ],
            [42 * mm, 34 * mm, 34 * mm, 22 * mm, 32 * mm],
        )
    else:
        story.append(Paragraph("No transactions recorded in the indexed dataset for this wallet.", body))

    section("4. Threat Intelligence Findings")
    threats = payload.get("threat_findings", [])
    if threats:
        table(
            ["Category", "Label", "Source", "Confidence", "Reference"],
            [[t.get("category", ""), t.get("label", ""), t.get("source", ""), f"{t.get('confidence', 0):.2f}", (t.get("reference_url") or "N/A")[:40]] for t in threats],
            [24 * mm, 46 * mm, 34 * mm, 18 * mm, 48 * mm],
        )
    else:
        story.append(Paragraph("No threat-intelligence matches for this wallet.", body))

    section("5. OSINT Correlation")
    osint_rows = [o for o in payload.get("osint_findings", []) if o.get("status") == "FOUND"]
    if osint_rows:
        table(
            ["Source", "Status", "Confidence", "Finding"],
            [[o.get("source_name", ""), o.get("status", ""), f"{o.get('confidence', 0):.2f}", str(o.get("finding", ""))[:70]] for o in osint_rows],
            [40 * mm, 22 * mm, 20 * mm, 88 * mm],
        )
    else:
        story.append(Paragraph("No automated OSINT findings reported for this wallet.", body))

    section("6. Fund Flow Trace")
    flow = payload.get("fund_flow") or {}
    path = flow.get("path") or []
    if path:
        story.append(Paragraph(" -> ".join(path), body))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Hops: {flow.get('hops', 0)}   |   Total observed flow: {flow.get('total_amount', 0)}", body))
        story.append(Paragraph("Note: shortest observed path in the available transaction graph; not a claim of true illicit-money flow.", note))
    else:
        story.append(Paragraph("No bounded fund-flow path was computed for this report.", body))

    section("7. Risk Indicators")
    table(
        ["Indicator", "Status", "Weight", "Evidence"],
        [[i.get("name", ""), i.get("status", ""), f"+{i.get('weight', 0)}", str(i.get("evidence", ""))[:80]] for i in risk.get("indicators", [])],
        [38 * mm, 22 * mm, 14 * mm, 90 * mm],
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Total score: {risk.get('score', 0)} / {risk.get('max_score', 0)}  -  Risk band: {risk.get('band', 'N/A')}", body))

    section("7b. Evidence")
    evidence = payload.get("evidence", [])
    if evidence:
        table(
            ["ID", "Type", "Title", "SHA-256 (truncated)"],
            [[str(e.get("id", "")), e.get("type", ""), e.get("title", ""), (e.get("sha256") or "N/A")[:24]] for e in evidence],
            [12 * mm, 26 * mm, 62 * mm, 70 * mm],
        )
    else:
        story.append(Paragraph("No evidence records attached.", body))

    section("7b. Investigation Timeline")
    timeline = payload.get("timeline", [])
    if timeline:
        table(
            ["Time", "Event", "Description"],
            [[str(e.get("created_at", "")), e.get("event_type", ""), str(e.get("description", ""))[:90]] for e in timeline[:40]],
            [30 * mm, 32 * mm, 108 * mm],
        )
    else:
        story.append(Paragraph("No timeline events recorded.", body))

    section("8. Analyst Notes")
    investigation = payload.get("investigation") or {}
    story.append(Paragraph(str(investigation.get("notes") or "No analyst notes recorded."), body))

    section("9. System Metadata")
    table(
        ["Field", "Value"],
        [
            ["Platform", f"ChainIntel v{payload.get('app_version', '')}"],
            ["Mode", payload.get("mode", "")],
            ["Generated at", payload.get("generated_at", "")],
            ["Report ID", payload.get("report_id", "")],
        ],
        [40 * mm, 120 * mm],
    )
    story.append(Spacer(1, 8))
    story.append(Paragraph("Important Notice: " + " ".join(REPORT_DISCLAIMERS), note))

    doc.build(story)
    return buffer.getvalue()


def render_csv(payload: dict[str, Any]) -> bytes:
    import pandas as pd

    rows = []
    for tx in payload.get("transactions", []):
        rows.append(
            {
                "tx_hash": tx.get("tx_hash"),
                "blockchain": tx.get("blockchain"),
                "from_address": tx.get("from_address"),
                "to_address": tx.get("to_address"),
                "amount": tx.get("amount"),
                "asset": tx.get("asset"),
                "timestamp": tx.get("timestamp"),
                "confirmations": tx.get("confirmations"),
                "status": tx.get("status"),
                "is_demo": tx.get("is_demo"),
            }
        )
    df = pd.DataFrame(rows, columns=["tx_hash", "blockchain", "from_address", "to_address", "amount", "asset", "timestamp", "confirmations", "status", "is_demo"])
    return df.to_csv(index=False).encode("utf-8")
