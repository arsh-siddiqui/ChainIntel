"""Alerts and monitoring endpoints.

NOTE: /monitors routes are declared before /{alert_id} routes so path
parameters never shadow the static segment.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import AppError, ok
from app.models import MonitoredWallet
from app.schemas.alert import AlertUpdate, MonitorCreate, MonitorUpdate
from app.services import monitoring
from app.services.alert_engine import list_alerts, update_alert
from app.services.audit import log_action
from app.services.serializers import alert_dict, monitor_dict
from app.utils.address_validation import validate_address

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def get_alerts(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None, pattern="^(NEW|ACKNOWLEDGED|INVESTIGATING|RESOLVED)$"),
    severity: str | None = Query(default=None, pattern="^(INFO|LOW|MEDIUM|HIGH|CRITICAL)$"),
    search: str | None = None,
    page: int = 1,
    page_size: int = 25,
):
    items, pagination = list_alerts(db, status=status, severity=severity, search=search, page=page, page_size=page_size)
    return ok(items, pagination)


@router.get("/monitors")
def get_monitors(db: Session = Depends(get_db)):
    monitors = monitoring.list_monitors(db)
    return ok([monitor_dict(m) for m in monitors], {"count": len(monitors)})


@router.post("/monitor")
def create_monitor(request: MonitorCreate, db: Session = Depends(get_db)):
    validation = validate_address(request.wallet_address)
    if not validation["valid"]:
        raise AppError(400, "INVALID_WALLET", validation["reason"])
    existing = (
        db.query(MonitoredWallet).filter(MonitoredWallet.wallet_address == request.wallet_address).one_or_none()
    )
    if existing:
        raise AppError(409, "MONITOR_EXISTS", f"{request.wallet_address} is already monitored.")
    monitor = monitoring.create_monitor(db, request.model_dump())
    log_action(db, "monitor_created", "monitored_wallet", monitor.id, {"wallet_address": request.wallet_address, "rules": request.rules})
    return ok(monitor_dict(monitor))


@router.patch("/monitors/{monitor_id}")
def update_monitor(monitor_id: int, request: MonitorUpdate, db: Session = Depends(get_db)):
    monitor = monitoring.get_monitor(db, monitor_id)
    if monitor is None:
        raise AppError(404, "MONITOR_NOT_FOUND", f"Monitor {monitor_id} does not exist.")
    monitor.status = request.status
    db.commit()
    log_action(db, "monitor_updated", "monitored_wallet", monitor.id, {"status": request.status})
    return ok(monitor_dict(monitor))


@router.delete("/monitors/{monitor_id}")
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = monitoring.get_monitor(db, monitor_id)
    if monitor is None:
        raise AppError(404, "MONITOR_NOT_FOUND", f"Monitor {monitor_id} does not exist.")
    db.delete(monitor)
    db.commit()
    log_action(db, "monitor_deleted", "monitored_wallet", monitor_id, {"wallet_address": monitor.wallet_address})
    return ok({"deleted": True, "id": monitor_id})


@router.patch("/{alert_id}")
def patch_alert(alert_id: int, request: AlertUpdate, db: Session = Depends(get_db)):
    alert = update_alert(db, alert_id, request.status)
    if alert is None:
        raise AppError(404, "ALERT_NOT_FOUND", f"Alert {alert_id} does not exist.")
    log_action(db, "alert_status_updated", "alert", alert.id, {"status": request.status})
    return ok(alert_dict(alert))
