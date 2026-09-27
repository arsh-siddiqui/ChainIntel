"""Settings endpoints. Never returns API key values - only configuration status."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.envelope import ok
from app.services import osint as osint_service
from app.services.blockchain.factory import provider_status_summary

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/providers")
def providers(db: Session = Depends(get_db)):
    return ok(
        {
            "mode": settings.app_mode.upper(),
            "blockchain_providers": provider_status_summary(),
            "osint_sources": osint_service.external_sources_status(),
            "osint_provider_enabled": settings.osint_provider_enabled,
            "note": (
                "ChainIntel runs against real blockchain APIs only. "
                "API key values are never returned by this endpoint - only configured/not-configured status."
            ),
        }
    )


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    from app.models import Alert, MonitoredWallet

    db_scheme = settings.database_url.split(":", 1)[0] if settings.database_url else "unknown"
    return ok(
        {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "mode": settings.app_mode.upper(),
            "database": {"engine": db_scheme, "url": f"{db_scheme}://<redacted>"},
            "monitoring": {
                "enabled": settings.monitoring_enabled,
                "poll_interval_seconds": settings.poll_interval_seconds,
                "active_monitors": db.query(MonitoredWallet).filter(MonitoredWallet.status == "ACTIVE").count(),
                "alerts_total": db.query(Alert).count(),
            },
            "limits": {
                "rate_limit_requests": settings.rate_limit_requests,
                "rate_limit_window_seconds": settings.rate_limit_window_seconds,
                "max_upload_mb": settings.max_upload_mb,
            },
            "evidence_dir": settings.evidence_dir,
            "cors_origins": settings.cors_origin_list,
        }
    )
