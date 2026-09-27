"""Shared serializers converting ORM models to API dicts."""
from __future__ import annotations

from app.models import (
    Alert,
    AuditLog,
    Case,
    CaseEvent,
    Evidence,
    Investigation,
    MonitoredWallet,
    OSINTFinding,
    Report,
    ThreatFinding,
    Transaction,
    Wallet,
)
from app.utils.datetime import iso


def tx_dict(tx: Transaction | dict) -> dict:
    def get(name, default=None):
        return tx.get(name, default) if isinstance(tx, dict) else getattr(tx, name, default)

    return {
        "tx_hash": get("tx_hash"),
        "blockchain": get("blockchain"),
        "from_address": get("from_address"),
        "to_address": get("to_address"),
        "amount": get("amount", 0.0),
        "asset": get("asset", "BTC"),
        "timestamp": iso(get("timestamp")),
        "block_number": get("block_number"),
        "confirmations": get("confirmations", 0),
        "status": get("status", "confirmed"),
        "fee": get("fee"),
        "direction": get("direction"),
        "is_demo": bool(get("is_demo", False)),
    }


def wallet_dict(w: Wallet) -> dict:
    return {
        "address": w.address,
        "blockchain": w.blockchain,
        "label": w.label,
        "balance": w.balance,
        "asset": w.asset,
        "first_seen": iso(w.first_seen),
        "last_seen": iso(w.last_seen),
        "transaction_count": w.transaction_count,
        "is_demo": w.is_demo,
        "created_at": iso(w.created_at),
    }


def threat_dict(f: ThreatFinding) -> dict:
    return {
        "id": f.id,
        "wallet_address": f.wallet_address,
        "blockchain": f.blockchain,
        "category": f.category,
        "label": f.label,
        "source": f.source,
        "reference_url": f.reference_url,
        "confidence": f.confidence,
        "first_seen": iso(f.first_seen),
        "last_seen": iso(f.last_seen),
        "notes": f.notes,
        "status": f.status,
        "is_demo": f.is_demo,
    }


def osint_dict(f: OSINTFinding) -> dict:
    return {
        "id": f.id,
        "wallet_address": f.wallet_address,
        "source": f.source,
        "source_category": f.source_category,
        "record_type": f.record_type,
        "finding": f.finding,
        "status": f.status,
        "confidence": f.confidence,
        "reference_url": f.reference_url,
        "notes": f.notes,
        "observed_at": iso(f.observed_at),
        "is_demo": f.is_demo,
    }


def investigation_summary(i: Investigation) -> dict:
    return {
        "id": i.id,
        "case_id": i.case_id,
        "title": i.title,
        "wallet_address": i.wallet_address,
        "blockchain": i.blockchain,
        "status": i.status,
        "risk_level": i.risk_level,
        "risk_score": i.risk_score,
        "investigator": i.investigator,
        "notes": i.notes,
        "created_at": iso(i.created_at),
        "updated_at": iso(i.updated_at),
    }


def case_dict(c: Case) -> dict:
    return {
        "id": c.id,
        "case_number": c.case_number,
        "title": c.title,
        "description": c.description,
        "status": c.status,
        "priority": c.priority,
        "investigator": c.investigator,
        "created_at": iso(c.created_at),
        "updated_at": iso(c.updated_at),
    }


def case_event_dict(e: CaseEvent) -> dict:
    return {"id": e.id, "case_id": e.case_id, "event_type": e.event_type, "description": e.description, "created_at": iso(e.created_at)}


def alert_dict(a: Alert) -> dict:
    return {
        "id": a.id,
        "wallet_address": a.wallet_address,
        "rule": a.rule,
        "transaction_hash": a.transaction_hash,
        "severity": a.severity,
        "status": a.status,
        "title": a.title,
        "message": a.message,
        "is_demo": a.is_demo,
        "created_at": iso(a.created_at),
    }


def monitor_dict(m: MonitoredWallet) -> dict:
    return {
        "id": m.id,
        "wallet_address": m.wallet_address,
        "blockchain": m.blockchain,
        "label": m.label,
        "rules": m.rules,
        "status": m.status,
        "last_checked": iso(m.last_checked),
        "last_tx_hash": m.last_tx_hash,
        "is_demo": m.is_demo,
        "created_at": iso(m.created_at),
    }


def evidence_dict(e: Evidence) -> dict:
    return {
        "id": e.id,
        "case_id": e.case_id,
        "type": e.type,
        "title": e.title,
        "description": e.description,
        "source": e.source,
        "file_name": e.file_name,
        "sha256": e.sha256,
        "size_bytes": e.size_bytes,
        "has_file": bool(e.file_path),
        "created_at": iso(e.created_at),
    }


def report_dict(r: Report, include_payload: bool = False) -> dict:
    data = {
        "id": r.id,
        "case_id": r.case_id,
        "wallet_address": r.wallet_address,
        "blockchain": r.blockchain,
        "title": r.title,
        "mode": r.mode,
        "created_at": iso(r.created_at),
    }
    if include_payload:
        data["payload"] = r.payload
    return data


def audit_dict(a: AuditLog) -> dict:
    return {
        "id": a.id,
        "action": a.action,
        "resource_type": a.resource_type,
        "resource_id": a.resource_id,
        "investigator": a.investigator,
        "metadata": a.metadata_json,
        "timestamp": iso(a.timestamp),
    }
