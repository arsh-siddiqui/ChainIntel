"""Report generation and export endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import AppError, ok
from app.schemas.report import ReportCreate
from app.services import report_service
from app.services.serializers import report_dict
from app.utils.address_validation import validate_address

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_reports(db: Session = Depends(get_db), page: int = 1, page_size: int = 20):
    items, pagination = report_service.list_reports(db, page=page, page_size=page_size)
    return ok(items, pagination)


@router.post("/generate")
def generate_report(request: ReportCreate, db: Session = Depends(get_db)):
    wallet = request.wallet_address
    if not wallet and request.case_id:
        from app.services.case_service import case_or_404

        case = case_or_404(db, request.case_id)
        investigations = [i for i in case_service_investigations(db, case.id)]
        if not investigations:
            raise AppError(400, "NO_INVESTIGATIONS", "The case has no wallet investigations to report on.")
        wallet = investigations[0].wallet_address
    if not wallet:
        raise AppError(400, "WALLET_REQUIRED", "Provide a wallet_address or a case_id with at least one linked investigation.")
    validation = validate_address(wallet)
    if not validation["valid"]:
        raise AppError(400, "INVALID_WALLET", validation["reason"])
    report = report_service.create_report(db, wallet, request.case_id, request.title)
    return ok(report_dict(report, include_payload=True))


def case_service_investigations(db: Session, case_id: int):
    from app.models import Investigation

    return db.query(Investigation).filter(Investigation.case_id == case_id).all()


@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise AppError(404, "REPORT_NOT_FOUND", f"Report {report_id} does not exist.")
    return ok(report_dict(report, include_payload=True))


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db), format: str = Query(default="pdf", pattern="^(pdf|json|csv)$")):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise AppError(404, "REPORT_NOT_FOUND", f"Report {report_id} does not exist.")
    if format == "json":
        import json

        return Response(
            content=json.dumps(report.payload, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{report.id}.json"'},
        )
    if format == "csv":
        return Response(
            content=report_service.render_csv(report.payload),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{report.id}.csv"'},
        )
    pdf_bytes = report_service.render_pdf(report.payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report.id}.pdf"'},
    )
