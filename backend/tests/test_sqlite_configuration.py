"""Tests verifying SQLite engine configuration, foreign keys, auto-directory creation, idempotent seeding, and migrations."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import ensure_db_directory, normalize_database_url, settings
from app.core.database import Base, SessionLocal, engine
from app.core.seed import normalize_wallet_address, seed_db
from app.models import (
    Alert,
    AuditLog,
    Case,
    CaseEvent,
    Evidence,
    Investigation,
    MonitoredWallet,
    OSINTFinding,
    Report,
    ThreatFinding,
    Transaction,
    Wallet,
)


def test_sqlite_dialect_and_pragmas(db_session):
    """Verify SQLite dialect and that foreign key constraints are enabled via PRAGMA."""
    assert engine.dialect.name == "sqlite"
    # check_same_thread=False verified in connect_args
    assert engine.url.query.get("check_same_thread") is None or engine.dialect.connect_args.get("check_same_thread") is False

    # Verify foreign_keys pragma is enabled on active connections
    result = db_session.execute(text("PRAGMA foreign_keys")).scalar()
    assert result == 1, "PRAGMA foreign_keys must be enabled (1)"


def test_sqlite_foreign_key_enforcement(db_session):
    """Verify that SQLite actively enforces foreign key integrity constraints."""
    orphan_event = CaseEvent(
        case_id=99999999,
        event_type="test_orphan",
        description="This event has an invalid foreign key",
    )
    db_session.add(orphan_event)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    orphan_evidence = Evidence(
        case_id=99999999,
        type="Analyst Note",
        title="Invalid FK Evidence",
    )
    db_session.add(orphan_evidence)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_directory_auto_creation():
    """Verify that SQLite and evidence directories are created automatically when missing."""
    temp_dir = tempfile.mkdtemp()
    try:
        deep_db_path = os.path.join(temp_dir, "nested", "sub", "test.db")
        assert not os.path.exists(os.path.dirname(deep_db_path))

        db_url = f"sqlite:///{deep_db_path}"
        ensure_db_directory(db_url)
        assert os.path.exists(os.path.dirname(deep_db_path))

        normalized = normalize_database_url(db_url)
        assert normalized.startswith("sqlite:///")

        deep_evidence_path = os.path.join(temp_dir, "deep_evidence", "uploads")
        assert not os.path.exists(deep_evidence_path)
        os.makedirs(deep_evidence_path, exist_ok=True)
        assert os.path.exists(deep_evidence_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_seed_db_idempotency_live_mode(db_session, monkeypatch):
    """Verify seeding in LIVE mode does NOT insert fictional demo wallets and is idempotent."""
    monkeypatch.setattr(settings, "app_mode", "LIVE")

    # Run seed_db once
    seed_db(db_session)
    counts_first = {
        "wallets": db_session.query(Wallet).filter(Wallet.is_demo == True).count(),
        "threats": db_session.query(ThreatFinding).count(),
        "osint": db_session.query(OSINTFinding).count(),
    }
    # Fictional demo wallets must NOT be inserted in LIVE mode
    assert counts_first["wallets"] == 0

    # Run seed_db a second time - must not fail or create duplicate rows
    seed_db(db_session)
    counts_second = {
        "wallets": db_session.query(Wallet).filter(Wallet.is_demo == True).count(),
        "threats": db_session.query(ThreatFinding).count(),
        "osint": db_session.query(OSINTFinding).count(),
    }
    assert counts_first == counts_second, f"Counts changed on re-seed: {counts_first} != {counts_second}"


def test_seed_db_idempotency_demo_mode(monkeypatch):
    """Verify seeding in DEMO mode inserts demo wallets and is strictly idempotent with ON CONFLICT DO NOTHING."""
    monkeypatch.setattr(settings, "app_mode", "DEMO")

    temp_dir = tempfile.mkdtemp()
    try:
        temp_db = os.path.join(temp_dir, "demo_seed_test.db")
        test_engine = create_engine(f"sqlite:///{temp_db}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(test_engine)
        test_session = Session(test_engine)

        try:
            # First seed run
            seed_db(test_session)
            wallets_first = test_session.query(Wallet).count()
            threats_first = test_session.query(ThreatFinding).count()
            txs_first = test_session.query(Transaction).count()
            assert wallets_first > 0, "DEMO mode should seed demo wallets"

            # Second seed run - must NOT raise sqlite3.IntegrityError: UNIQUE constraint failed
            seed_db(test_session)
            wallets_second = test_session.query(Wallet).count()
            threats_second = test_session.query(ThreatFinding).count()
            txs_second = test_session.query(Transaction).count()

            assert wallets_first == wallets_second
            assert threats_first == threats_second
            assert txs_first == txs_second
        finally:
            test_session.close()
            test_engine.dispose()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_init_db_cli_command_twice():
    """Verify executing python -m app.core.init_db twice consecutively is 100% error-free."""
    temp_dir = tempfile.mkdtemp()
    try:
        temp_db = os.path.join(temp_dir, "init_cli_test.db")
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{temp_db.replace(os.sep, '/')}"
        env["PYTHONPATH"] = backend_dir
        env["APP_MODE"] = "DEMO"

        # First run
        res1 = subprocess.run(
            [sys.executable, "-m", "app.core.init_db"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        assert res1.returncode == 0, f"First init_db failed: {res1.stderr}\n{res1.stdout}"

        # Second run immediately after
        res2 = subprocess.run(
            [sys.executable, "-m", "app.core.init_db"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        assert res2.returncode == 0, f"Second init_db failed: {res2.stderr}\n{res2.stdout}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_app_startup_with_populated_database():
    """Verify FastAPI application startup completes cleanly with an existing populated SQLite database."""
    from app.main import app

    # Booting the app runs lifespan (init_db(seed=False))
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["data"]["database"] == "connected"

        res_overview = client.get("/api/settings/overview")
        assert res_overview.status_code == 200
        assert res_overview.json()["data"]["database"]["engine"] == "sqlite"


def test_crud_all_models_sqlite(db_session):
    """Verify full CRUD lifecycle across core models on SQLite."""
    test_case = Case(
        case_number="CASE-TEST-SQLITE-01",
        title="SQLite Test Case",
        description="Testing CRUD on SQLite",
        status="OPEN",
        priority="LOW",
        investigator="Test Investigator",
    )
    db_session.add(test_case)
    db_session.commit()
    assert test_case.id is not None

    event = CaseEvent(
        case_id=test_case.id,
        event_type="test_event",
        description="Created test event",
    )
    db_session.add(event)
    db_session.commit()
    assert event.id is not None

    ev = Evidence(
        case_id=test_case.id,
        type="Analyst Note",
        title="SQLite Evidence",
        content_text="Sample text content for integrity",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        size_bytes=32,
    )
    db_session.add(ev)
    db_session.commit()
    assert ev.id is not None

    inv = Investigation(
        case_id=test_case.id,
        title="SQLite Investigation",
        wallet_address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        blockchain="bitcoin",
        status="COMPLETED",
        risk_level="LOW",
        risk_score=10.0,
        investigator="Test Analyst",
    )
    db_session.add(inv)
    db_session.commit()
    assert inv.id is not None

    rep = Report(
        id="test-report-sqlite-uuid-001",
        case_id=test_case.id,
        wallet_address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        blockchain="bitcoin",
        title="Test Report",
        mode="LIVE",
        payload={"summary": "all clear"},
    )
    db_session.add(rep)
    db_session.commit()
    assert rep.id == "test-report-sqlite-uuid-001"

    # Cleanup test records (delete referencing children first to respect SQLite foreign keys)
    db_session.delete(rep)
    db_session.delete(inv)
    db_session.delete(ev)
    db_session.delete(event)
    db_session.flush()
    db_session.delete(test_case)
    db_session.commit()


def test_alembic_migrations_sqlite():
    """Verify that Alembic migrations run cleanly against SQLite (upgrade head and downgrade base)."""
    temp_dir = tempfile.mkdtemp()
    try:
        temp_db = os.path.join(temp_dir, "migration_test.db")
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{temp_db.replace(os.sep, '/')}"
        env["PYTHONPATH"] = backend_dir

        # 1. Run alembic upgrade head
        up_res = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        assert up_res.returncode == 0, f"alembic upgrade head failed: {up_res.stderr}\n{up_res.stdout}"

        # Verify tables exist in SQLite
        import sqlite3
        con = sqlite3.connect(temp_db)
        cur = con.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        con.close()
        expected = ["wallets", "transactions", "threat_findings", "osint_findings", "cases", "case_events", "alerts", "monitored_wallets", "evidence", "investigations", "reports", "audit_log", "alembic_version"]
        for exp in expected:
            assert exp in tables, f"Expected table {exp} missing in migrated SQLite schema"

        # 2. Run alembic downgrade base
        down_res = subprocess.run(
            ["alembic", "downgrade", "base"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        assert down_res.returncode == 0, f"alembic downgrade base failed: {down_res.stderr}\n{down_res.stdout}"

        # Verify tables are dropped
        con = sqlite3.connect(temp_db)
        cur = con.cursor()
        remaining = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        con.close()
        for exp in ["wallets", "transactions", "cases", "reports"]:
            assert exp not in remaining, f"Table {exp} should have been dropped on downgrade"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
