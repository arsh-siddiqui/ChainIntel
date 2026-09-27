"""Audit logging service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.utils.pagination import clamp, meta


def log_action(
    db: Session,
    action: str,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    meta_data: dict | None = None,
    investigator: str = "Investigator",
) -> None:
    db.add(
        AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            metadata_json=meta_data,
            investigator=investigator,
        )
    )
    db.commit()


def list_audit(db: Session, page: int = 1, page_size: int = 25, action: str | None = None):
    page, page_size = clamp(page, page_size)
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    total = query.count()
    items = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, meta(page, page_size, total)
