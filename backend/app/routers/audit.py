"""Audit log endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import ok
from app.services.audit import list_audit
from app.services.serializers import audit_dict

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("")
def get_audit_log(
    db: Session = Depends(get_db),
    action: str | None = None,
    page: int = 1,
    page_size: int = Query(default=25, le=100),
):
    items, pagination = list_audit(db, page=page, page_size=page_size, action=action)
    return ok([audit_dict(a) for a in items], pagination)
