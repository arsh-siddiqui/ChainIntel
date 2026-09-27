"""ChainIntel API entrypoint.

Run with: uvicorn app.main:app --reload --port 8000  (from the backend/ directory)
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import init_db
from app.core.envelope import (
    AppError,
    app_error_handler,
    http_exception_handler,
    ok,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import get_logger, setup_logging
from app.core.security import RateLimitMiddleware, RequestSizeLimitMiddleware
from app.routers import (
    alerts,
    audit,
    cases,
    dashboard,
    evidence,
    graph,
    osint,
    reports,
    search,
    settings as settings_router,
    threats,
    transactions,
    wallets,
)

setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    stop_event = asyncio.Event()
    monitor_task = None
    if settings.monitoring_enabled:
        from app.services.monitoring import monitor_loop

        monitor_task = asyncio.create_task(monitor_loop(stop_event))
    logger.info("ChainIntel started (mode=%s)", settings.app_mode.upper())
    yield
    if monitor_task is not None:
        stop_event.set()
        monitor_task.cancel()
    logger.info("ChainIntel shutdown complete")


app = FastAPI(
    title="ChainIntel API",
    description="Blockchain OSINT & Cryptocurrency Forensics Platform - backend API",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware (outermost first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware)

# Exception handlers -> consistent envelope
app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppError, app_error_handler)

# Routers
for router in (
    dashboard.router,
    wallets.router,
    transactions.router,
    graph.router,
    threats.router,
    osint.router,
    alerts.router,
    cases.router,
    evidence.router,
    reports.router,
    settings_router.router,
    search.router,
    audit.router,
):
    app.include_router(router, prefix="/api")


@app.get("/api/health")
def health():
    from app.core.database import engine
    from sqlalchemy import text

    database = "connected"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - health must never raise
        database = "unavailable"
    return ok(
        {
            "status": "healthy" if database == "connected" else "degraded",
            "mode": settings.app_mode.upper(),
            "version": settings.app_version,
            "database": database,
        }
    )


@app.get("/api")
def api_root():
    return ok({"name": settings.app_name, "docs": "/docs", "health": "/api/health"})
