"""Dashboard aggregation endpoints."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import ok
from app.models import Alert, Case, Investigation, MonitoredWallet, Report, ThreatFinding, Transaction
from app.services.serializers import alert_dict, investigation_summary
from app.utils.datetime import utcnow

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_investigations = db.query(Investigation).count()
    suspicious_wallets = db.query(func.count(func.distinct(ThreatFinding.wallet_address))).scalar() or 0
    transactions_analyzed = db.query(Transaction).count()
    active_alerts = db.query(Alert).filter(Alert.status.in_(["NEW", "ACKNOWLEDGED", "INVESTIGATING"])).count()
    threat_matches = db.query(ThreatFinding).count()
    wallets_monitored = db.query(MonitoredWallet).filter(MonitoredWallet.status == "ACTIVE").count()
    open_cases = db.query(Case).filter(Case.status.in_(["OPEN", "UNDER_INVESTIGATION"])).count()
    reports_generated = db.query(Report).count()

    # Transaction activity over the last 30 days.
    cutoff = utcnow() - timedelta(days=30)
    recent = db.query(Transaction).filter(Transaction.timestamp >= cutoff).all()
    activity: dict[str, dict] = defaultdict(lambda: {"incoming": 0.0, "outgoing": 0.0, "count": 0})
    for tx in recent:
        day = tx.timestamp.date().isoformat()
        activity[day]["count"] += 1
        if tx.to_address:
            activity[day]["incoming"] += tx.amount or 0.0
        if tx.from_address:
            activity[day]["outgoing"] += tx.amount or 0.0
    days = [(utcnow() - timedelta(days=offset)).date() for offset in range(29, -1, -1)]
    activity_series = [
        {
            "date": day.isoformat(),
            "incoming": round(activity[day.isoformat()]["incoming"], 4),
            "outgoing": round(activity[day.isoformat()]["outgoing"], 4),
            "count": activity[day.isoformat()]["count"],
        }
        for day in days
    ]

    # Threat category distribution.
    category_counts: dict[str, int] = defaultdict(int)
    for (category,) in db.query(ThreatFinding.category).all():
        category_counts[category] += 1
    threat_distribution = [{"category": c, "count": n} for c, n in sorted(category_counts.items(), key=lambda kv: -kv[1])]

    # Investigation risk-level distribution.
    risk_counts: dict[str, int] = defaultdict(int)
    status_counts: dict[str, int] = defaultdict(int)
    for risk, status in db.query(Investigation.risk_level, Investigation.status).all():
        if risk:
            risk_counts[risk] += 1
        status_counts[status or "UNKNOWN"] += 1
    risk_distribution = [{"risk_level": k, "count": v} for k, v in risk_counts.items()]
    status_distribution = [{"status": k, "count": v} for k, v in status_counts.items()]

    # Top suspicious counterparties: threat-flagged wallets ranked by observed transaction volume.
    threat_wallets = [row[0] for row in db.query(ThreatFinding.wallet_address).distinct().all()]
    counterparties = []
    for address in threat_wallets:
        txs = (
            db.query(Transaction)
            .filter((Transaction.from_address == address) | (Transaction.to_address == address))
            .all()
        )
        if not txs:
            continue
        counterparties.append(
            {
                "address": address,
                "transactions": len(txs),
                "volume": round(sum(t.amount or 0.0 for t in txs), 4),
            }
        )
    counterparties.sort(key=lambda c: -c["transactions"])
    top_counterparties = counterparties[:6]

    recent_investigations = (
        db.query(Investigation).order_by(Investigation.created_at.desc()).limit(8).all()
    )
    recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(6).all()

    return ok(
        {
            "kpis": {
                "total_investigations": total_investigations,
                "suspicious_wallets": suspicious_wallets,
                "transactions_analyzed": transactions_analyzed,
                "active_alerts": active_alerts,
                "threat_matches": threat_matches,
                "wallets_monitored": wallets_monitored,
                "open_cases": open_cases,
                "reports_generated": reports_generated,
            },
            "activity": activity_series,
            "threat_distribution": threat_distribution,
            "risk_distribution": risk_distribution,
            "investigation_status": status_distribution,
            "top_counterparties": top_counterparties,
            "recent_investigations": [investigation_summary(i) for i in recent_investigations],
            "recent_alerts": [alert_dict(a) for a in recent_alerts],
        },
        {"mode": "LIVE"},
    )
