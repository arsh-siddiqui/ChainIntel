"""Threat intelligence endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import AppError, ok
from app.models import THREAT_CATEGORIES
from app.services import threat_intelligence
from app.services.audit import log_action
from app.services.serializers import threat_dict

router = APIRouter(prefix="/threats", tags=["threats"])


@router.get("")
def list_threats(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, max_length=255),
    category: str | None = None,
    source: str | None = None,
    page: int = 1,
    page_size: int = 25,
):
    items, pagination = threat_intelligence.list_threats(db, search=search, category=category, source=source, page=page, page_size=page_size)
    return ok([threat_dict(t) for t in items], pagination)


@router.get("/stats")
def threat_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func

    from app.models import ThreatFinding

    total = db.query(ThreatFinding).count()
    flagged_wallets = db.query(func.count(func.distinct(ThreatFinding.wallet_address))).scalar() or 0
    sources = [
        {"source": row[0], "count": row[1]}
        for row in db.query(ThreatFinding.source, func.count()).group_by(ThreatFinding.source).all()
    ]
    return ok(
        {
            "total": total,
            "flagged_wallets": flagged_wallets,
            "categories": threat_intelligence.category_stats(db),
            "sources": sources,
            "allowed_categories": THREAT_CATEGORIES,
        }
    )


@router.post("/import")
async def import_threats(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    content = await file.read()
    if not content:
        raise AppError(400, "EMPTY_FILE", "The uploaded file is empty.")
    records = threat_intelligence.parse_import_file(file.filename or "", content)
    if not records:
        raise AppError(400, "IMPORT_EMPTY", "No records found in the uploaded file.")
    stats = threat_intelligence.import_records(db, records)
    log_action(db, "threat_database_imported", "threat_database", file.filename, {k: v for k, v in stats.items() if k != "errors"})
    return ok(stats)
