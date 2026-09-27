"""Alert engine: rule evaluation and alert lifecycle management."""
from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Alert, MonitoredWallet, ThreatFinding
from app.services.serializers import alert_dict
from app.utils.pagination import clamp, meta


def evaluate_rules(
    rules: dict[str, Any],
    tx: dict[str, Any],
    focus_address: str,
    threat_match: bool = False,
    flagged_counterparty: bool = False,
) -> tuple[bool, str, str]:
    """Evaluate monitoring rules against a transaction.

    Returns (triggered, severity, reason).
    """
    direction = (rules.get("direction") or "any").lower()
    tx_direction = tx.get("direction") or ("outgoing" if tx.get("from_address") == focus_address else "incoming")
    if direction in ("incoming", "outgoing") and tx_direction != direction:
        return False, "LOW", ""

    threshold = rules.get("amount_threshold")
    reasons: list[str] = []
    triggered = False
    severity = "LOW"

    if threshold is not None:
        try:
            if float(tx.get("amount", 0.0)) >= float(threshold):
                triggered = True
                reasons.append(f"amount {tx.get('amount')} {tx.get('asset', '')} exceeded threshold {threshold}".strip())
                severity = "MEDIUM"
        except (TypeError, ValueError):
            pass

    if rules.get("on_threat_match") and threat_match:
        triggered = True
        reasons.append("wallet has a threat-intelligence match")
        severity = "CRITICAL"

    if rules.get("flagged_counterparty") and flagged_counterparty:
        triggered = True
        reasons.append("counterparty carries a threat-intelligence record")
        severity = max(severity, "HIGH", key=lambda s: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(s))

    if not threshold and not rules.get("on_threat_match") and not rules.get("flagged_counterparty"):
        # No criteria configured: alert on any matching-direction transaction.
        triggered = True
        reasons.append(f"any {tx_direction} transaction")
        severity = "INFO"

    if not triggered:
        return False, "LOW", ""
    return True, severity, f"{tx_direction.capitalize()} transaction: " + "; ".join(reasons)


def create_alert(
    db: Session,
    wallet_address: str,
    rule: dict[str, Any],
    tx: dict[str, Any] | None,
    severity: str,
    message: str,
    is_demo: bool,
    title_prefix: str = "Monitoring alert",
) -> Alert | None:
    tx_hash = (tx or {}).get("tx_hash")
    # Deduplicate: same wallet + transaction hash, unless the previous alert was resolved.
    if tx_hash:
        existing = (
            db.query(Alert)
            .filter(Alert.wallet_address == wallet_address, Alert.transaction_hash == tx_hash, Alert.status != "RESOLVED")
            .one_or_none()
        )
        if existing:
            return None
    alert = Alert(
        wallet_address=wallet_address,
        rule=rule,
        transaction_hash=tx_hash,
        severity=severity,
        status="NEW",
        title=title_prefix,
        message=message,
        is_demo=is_demo,
    )
    db.add(alert)
    db.commit()
    return alert


def list_alerts(
    db: Session,
    status: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 25,
):
    page, page_size = clamp(page, page_size)
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Alert.wallet_address.ilike(like), Alert.title.ilike(like), Alert.message.ilike(like)))
    total = query.count()
    items = query.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [alert_dict(a) for a in items], meta(page, page_size, total)


def update_alert(db: Session, alert_id: int, status: str) -> Alert | None:
    alert = db.query(Alert).filter(Alert.id == alert_id).one_or_none()
    if alert is None:
        return None
    alert.status = status
    db.commit()
    return alert


def threat_context_for(db: Session, address: str) -> tuple[bool, bool]:
    """(focus_has_threat_records, counterparties_flagged) used by rule evaluation."""
    focus_match = db.query(ThreatFinding.id).filter(ThreatFinding.wallet_address == address).first() is not None
    return focus_match, focus_match
