"""Evidence repository endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import AppError, ok
from app.models import EVIDENCE_TYPES
from app.services import evidence_service
from app.services.serializers import evidence_dict

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("")
def list_evidence(
    db: Session = Depends(get_db),
    case_id: int | None = None,
    type: str | None = Query(default=None, alias="type"),
    search: str | None = None,
    page: int = 1,
    page_size: int = 25,
):
    items, pagination = evidence_service.list_evidence(db, case_id=case_id, evidence_type=type, search=search, page=page, page_size=page_size)
    return ok(items, {**pagination, "evidence_types": EVIDENCE_TYPES})


@router.get("/{evidence_id}")
def get_evidence(evidence_id: int, db: Session = Depends(get_db)):
    evidence = evidence_service.get_evidence(db, evidence_id)
    if evidence is None:
        raise AppError(404, "EVIDENCE_NOT_FOUND", f"Evidence {evidence_id} does not exist.")
    data = evidence_dict(evidence)
    data["integrity_verified"] = evidence_service.verify_integrity(db, evidence)
    return ok(data)


@router.get("/{evidence_id}/download")
def download_evidence(evidence_id: int, db: Session = Depends(get_db)):
    path, filename = evidence_service.download_evidence(db, evidence_id)
    return FileResponse(path, filename=filename, media_type="application/octet-stream")
