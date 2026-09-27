"""Investigation case management service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.envelope import AppError
from app.models import Case, CaseEvent, Investigation
from app.services.audit import log_action
from app.services.serializers import case_dict, case_event_dict
from app.utils.datetime import utcnow


def create_case(db: Session, payload: dict) -> Case:
    year = utcnow().year
    sequence = db.query(Case).count() + 1
    while True:
        case_number = f"CASE-{year}-{sequence:03d}"
        if db.query(Case).filter(Case.case_number == case_number).one_or_none() is None:
            break
        sequence += 1
    case = Case(
        case_number=case_number,
        title=payload["title"],
        description=payload.get("description"),
        status=payload.get("status", "OPEN"),
        priority=payload.get("priority", "MEDIUM"),
        investigator=payload.get("investigator", "Investigator"),
    )
    db.add(case)
    db.commit()
    add_event(db, case.id, "case_created", f"Case {case.case_number} created ({case.priority.lower()} priority).")
    log_action(db, "case_created", "case", case.id, {"case_number": case.case_number})
    return case


def update_case(db: Session, case: Case, payload: dict) -> Case:
    changed = []
    for field in ("title", "description", "status", "priority"):
        if payload.get(field) is not None and getattr(case, field) != payload[field]:
            setattr(case, field, payload[field])
            changed.append(field)
    db.commit()
    if "status" in changed:
        add_event(db, case.id, "status_changed", f"Case status changed to {case.status}.")
    if changed:
        log_action(db, "case_updated", "case", case.id, {"fields": changed})
    return case


def add_event(db: Session, case_id: int, event_type: str, description: str) -> CaseEvent:
    event = CaseEvent(case_id=case_id, event_type=event_type, description=description)
    db.add(event)
    db.commit()
    return event


def get_case(db: Session, case_id: int) -> Case | None:
    return db.query(Case).filter(Case.id == case_id).one_or_none()


def case_detail(db: Session, case: Case) -> dict:
    investigations = db.query(Investigation).filter(Investigation.case_id == case.id).order_by(Investigation.created_at.desc()).all()
    from app.models import Evidence, Report
    from app.services.serializers import evidence_dict, investigation_summary, report_dict

    evidence = db.query(Evidence).filter(Evidence.case_id == case.id).order_by(Evidence.created_at.desc()).all()
    reports = db.query(Report).filter(Report.case_id == case.id).order_by(Report.created_at.desc()).all()
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at.asc()).all()
    return {
        **case_dict(case),
        "investigations": [investigation_summary(i) for i in investigations],
        "evidence": [evidence_dict(e) for e in evidence],
        "reports": [report_dict(r) for r in reports],
        "timeline": [case_event_dict(e) for e in events],
    }


def list_cases(db: Session, status: str | None = None, search: str | None = None, page: int = 1, page_size: int = 20):
    from app.utils.pagination import clamp, meta

    page, page_size = clamp(page, page_size)
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    if search:
        like = f"%{search}%"
        query = query.filter(Case.title.ilike(like) | Case.case_number.ilike(like) | Case.description.ilike(like))
    total = query.count()
    items = query.order_by(Case.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [case_dict(c) for c in items], meta(page, page_size, total)


async def link_investigation(db: Session, case: Case, wallet_address: str, investigator: str = "Investigator") -> Investigation:
    """Attach the latest investigation for a wallet, running one if none exists."""
    from app.services.wallet_analysis import run_investigation

    investigation = (
        db.query(Investigation)
        .filter(Investigation.wallet_address == wallet_address)
        .order_by(Investigation.created_at.desc())
        .first()
    )
    if investigation is None:
        investigation_payload = await run_investigation(db, wallet_address, investigator=investigator)
        investigation = db.query(Investigation).filter(Investigation.id == investigation_payload["investigation_id"]).one()
    investigation.case_id = case.id
    db.commit()
    add_event(db, case.id, "wallet_added", f"Investigation of {wallet_address} (risk: {investigation.risk_level or 'n/a'}) linked to case.")
    log_action(db, "case_investigation_linked", "case", case.id, {"wallet_address": wallet_address, "investigation_id": investigation.id})
    return investigation


def case_or_404(db: Session, case_id: int) -> Case:
    case = get_case(db, case_id)
    if case is None:
        raise AppError(404, "CASE_NOT_FOUND", f"Case {case_id} does not exist.")
    return case
