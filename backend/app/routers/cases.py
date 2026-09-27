"""Investigation case endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import ok
from app.models import EVIDENCE_TYPES
from app.schemas.investigation import CaseCreate, CaseInvestigationLink, CaseNoteCreate, CaseUpdate
from app.services import case_service, evidence_service
from app.services.serializers import case_dict, case_event_dict, evidence_dict

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("")
def list_cases(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None, pattern="^(OPEN|UNDER_INVESTIGATION|ON_HOLD|RESOLVED|CLOSED)$"),
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    items, pagination = case_service.list_cases(db, status=status, search=search, page=page, page_size=page_size)
    return ok(items, pagination)


@router.post("")
def create_case(request: CaseCreate, db: Session = Depends(get_db)):
    case = case_service.create_case(db, request.model_dump())
    return ok(case_service.case_detail(db, case))


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = case_service.case_or_404(db, case_id)
    return ok(case_service.case_detail(db, case))


@router.patch("/{case_id}")
def update_case(case_id: int, request: CaseUpdate, db: Session = Depends(get_db)):
    case = case_service.case_or_404(db, case_id)
    case = case_service.update_case(db, case, request.model_dump(exclude_none=True))
    return ok(case_service.case_detail(db, case))


@router.post("/{case_id}/investigations")
async def link_investigation(case_id: int, request: CaseInvestigationLink, db: Session = Depends(get_db)):
    case = case_service.case_or_404(db, case_id)
    investigation = await case_service.link_investigation(db, case, request.wallet_address)
    return ok({"investigation_id": investigation.id, "wallet_address": request.wallet_address})


@router.post("/{case_id}/notes")
def add_case_note(case_id: int, request: CaseNoteCreate, db: Session = Depends(get_db)):
    case = case_service.case_or_404(db, case_id)
    event = case_service.add_event(db, case.id, "analyst_note", request.note)
    return ok(case_event_dict(event))


@router.post("/{case_id}/evidence")
async def upload_case_evidence(
    case_id: int,
    db: Session = Depends(get_db),
    file: UploadFile | None = File(default=None),
    evidence_type: str = Form(default="Document"),
    title: str = Form(...),
    description: str | None = Form(default=None),
    source: str | None = Form(default=None),
    content_text: str | None = Form(default=None),
):
    case = case_service.case_or_404(db, case_id)
    if evidence_type not in EVIDENCE_TYPES:
        evidence_type = "Document"
    if file is not None and file.filename:
        content = await file.read()
        evidence = evidence_service.save_upload(
            db,
            case_id=case.id,
            evidence_type=evidence_type,
            title=title,
            description=description,
            source=source,
            filename=file.filename,
            content=content,
        )
    else:
        evidence = evidence_service.save_note(
            db,
            case_id=case.id,
            evidence_type=evidence_type if evidence_type != "Document" else "Analyst Note",
            title=title,
            description=description,
            source=source,
            content_text=content_text or "",
        )
    case_service.add_event(db, case.id, "evidence_attached", f"Evidence attached: {title} ({evidence.type}).")
    return ok(evidence_dict(evidence))
