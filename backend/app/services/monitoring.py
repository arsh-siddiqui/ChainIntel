"""Monitoring engine.

Polls each ACTIVE monitored wallet's provider at a bounded interval, evaluates
rules on genuinely retrieved transactions and stores progress (last_checked /
last_tx_hash). Provider failures are logged and retried on the next cycle -
no synthetic data is ever injected.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models import MonitoredWallet, ThreatFinding, Transaction
from app.services.alert_engine import create_alert, evaluate_rules
from app.services.serializers import monitor_dict
from app.utils.datetime import utcnow

logger = get_logger("monitoring")

MIN_LIVE_POLL_SECONDS = 45


def _threat_flags(db: Session, address: str, counterparty: str | None) -> tuple[bool, bool]:
    focus_flagged = db.query(ThreatFinding.id).filter(ThreatFinding.wallet_address == address).first() is not None
    cp_flagged = (
        counterparty is not None
        and db.query(ThreatFinding.id).filter(ThreatFinding.wallet_address == counterparty).first() is not None
    )
    return focus_flagged, cp_flagged


async def _poll_live_wallet(db: Session, monitor: MonitoredWallet) -> int:
    from app.services.blockchain.factory import get_provider
    from app.services.blockchain.base import ProviderError
    from app.services.wallet_analysis import _persist_transactions

    if monitor.last_checked and (utcnow() - monitor.last_checked) < timedelta(seconds=MIN_LIVE_POLL_SECONDS):
        return 0
    alerts_created = 0
    try:
        provider = get_provider(monitor.blockchain)
        txs = await provider.get_transactions(monitor.wallet_address, limit=25)
    except ProviderError as exc:
        if exc.code == "NOT_FOUND":
            logger.debug("Monitor %s: no on-chain records found (%s)", monitor.wallet_address, exc.message)
        else:
            logger.warning("Monitor %s provider error: %s", monitor.wallet_address, exc.message)
        monitor.last_checked = utcnow()
        db.commit()
        return 0

    known = {
        row[0]
        for row in db.query(Transaction.tx_hash)
        .filter(or_(Transaction.from_address == monitor.wallet_address, Transaction.to_address == monitor.wallet_address))
        .all()
    }
    for tx in txs:
        if tx["tx_hash"] in known or tx["tx_hash"] == monitor.last_tx_hash:
            continue
        direction = "outgoing" if tx.get("from_address") == monitor.wallet_address else "incoming"
        tx["direction"] = direction
        _persist_transactions(db, monitor.blockchain, [tx])
        counterparty = tx.get("to_address") if direction == "outgoing" else tx.get("from_address")
        threat_match, flagged_cp = _threat_flags(db, monitor.wallet_address, counterparty)
        triggered, severity, reason = evaluate_rules(monitor.rules or {}, tx, monitor.wallet_address, threat_match, flagged_cp)
        monitor.last_tx_hash = tx["tx_hash"]
        if triggered:
            alert = create_alert(
                db,
                monitor.wallet_address,
                monitor.rules,
                tx,
                severity,
                f"Live monitoring event: {reason}. Transaction {tx['tx_hash']} ({tx['amount']} {tx['asset']}).",
                is_demo=False,
                title_prefix="Live monitoring alert",
            )
            if alert:
                alerts_created += 1
    monitor.last_checked = utcnow()
    db.commit()
    return alerts_created


async def run_monitoring_cycle(db: Session) -> dict[str, Any]:
    monitors = db.query(MonitoredWallet).filter(MonitoredWallet.status == "ACTIVE").all()
    summary = {"checked": 0, "alerts_created": 0, "skipped": 0}
    for monitor in monitors:
        summary["checked"] += 1
        try:
            created = await _poll_live_wallet(db, monitor)
            summary["alerts_created"] += created
        except Exception:  # noqa: BLE001 - monitoring must never crash the app
            logger.exception("Monitoring cycle failed for %s", monitor.wallet_address)
            summary["skipped"] += 1
    return summary


async def monitor_loop(stop_event: asyncio.Event) -> None:
    logger.info("Monitoring engine started (interval=%ss, mode=%s)", settings.poll_interval_seconds, settings.app_mode)
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                summary = await run_monitoring_cycle(db)
                if summary["alerts_created"]:
                    logger.info("Monitoring cycle: %s", summary)
            finally:
                db.close()
        except Exception:  # noqa: BLE001
            logger.exception("Monitoring loop error")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.poll_interval_seconds)
        except asyncio.TimeoutError:
            continue
    logger.info("Monitoring engine stopped")


def get_monitor(db: Session, monitor_id: int) -> MonitoredWallet | None:
    return db.query(MonitoredWallet).filter(MonitoredWallet.id == monitor_id).one_or_none()


def create_monitor(db: Session, payload: dict[str, Any]) -> MonitoredWallet:
    monitor = MonitoredWallet(
        wallet_address=payload["wallet_address"],
        blockchain=payload.get("blockchain", "bitcoin"),
        label=payload.get("label"),
        rules=payload.get("rules", {}),
        status="ACTIVE",
        last_checked=None,
        is_demo=False,
    )
    db.add(monitor)
    db.commit()
    return monitor


def list_monitors(db: Session) -> list[MonitoredWallet]:
    return db.query(MonitoredWallet).order_by(MonitoredWallet.created_at.desc()).all()


def serialize_monitor(monitor: MonitoredWallet) -> dict:
    return monitor_dict(monitor)
