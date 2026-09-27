"""API routers. Each domain lives in its own module; logic stays in services."""
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

__all__ = [
    "alerts",
    "audit",
    "cases",
    "dashboard",
    "evidence",
    "graph",
    "osint",
    "reports",
    "search",
    "settings_router",
    "threats",
    "transactions",
    "wallets",
]
