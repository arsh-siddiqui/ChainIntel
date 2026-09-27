"""OSINT endpoints: provider correlation and restricted-source (dark-web) records."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import ok
from app.schemas.osint import RestrictedSourceCreate
from app.services import osint as osint_service
from app.services.audit import log_action
from app.services.serializers import osint_dict
from app.utils.address_validation import validate_address

router = APIRouter(prefix="/osint", tags=["osint"])


@router.get("/sources")
def osint_sources():
    return ok(
        {
            "sources": osint_service.external_sources_status(),
            "note": "Link-only sources cannot be queried automatically; they expose external search URLs instead.",
        }
    )


@router.get("/search/{address}")
def search_address(address: str, db: Session = Depends(get_db)):
    validation = validate_address(address)
    correlation = osint_service.correlate_wallet(address)
    return ok(
        {
            "validation": validation,
            "correlation": correlation,
            "restricted_count": len(osint_service.restricted_findings(db, address)),
        }
    )


@router.get("/restricted/{address}")
def restricted_records(address: str, db: Session = Depends(get_db)):
    rows = osint_service.restricted_findings(db, address)
    return ok(
        {
            "records": [osint_dict(r) for r in rows],
            "disclaimer": (
                "ChainIntel does not crawl the dark web. Restricted-source records exist only when imported "
                "intelligence or analyst notes are explicitly added. Absence of records means no configured "
                "restricted source has reported anything for this address."
            ),
        }
    )


@router.post("/restricted")
def add_restricted_record(request: RestrictedSourceCreate, db: Session = Depends(get_db)):
    finding = osint_service.add_restricted_record(db, request.model_dump())
    log_action(db, "restricted_source_record_added", "osint_finding", finding.id, {"wallet_address": request.wallet_address, "record_type": request.record_type})
    return ok(osint_dict(finding))
