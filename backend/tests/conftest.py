"""Shared test fixtures. Environment must be configured before app imports.

Tests are hermetic: they run in LIVE mode with NO real API keys configured,
and a deterministic FakeProvider is monkeypatched into the provider factory
wherever blockchain data is needed. No test ever touches a real API.
"""
from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///./data/test_chainintel.db"
os.environ["APP_MODE"] = "LIVE"
os.environ["MONITORING_ENABLED"] = "false"
os.environ["ETHERSCAN_API_KEY"] = ""
os.environ["MORALIS_API_KEY"] = ""
os.environ["ANKR_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.core.database import Base, SessionLocal, engine, init_db

    init_db()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def db_session(client):
    """Direct DB session for service-level tests."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
