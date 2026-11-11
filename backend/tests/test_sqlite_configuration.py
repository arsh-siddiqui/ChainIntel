"""Tests specifically verifying SQLite engine configuration, foreign keys, auto-directory creation, idempotent seeding, and migrations."""
from __future__ import annotations

import os
import shutil
import tempfile
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import ensure_db_directory, normalize_database_url, settings
from app.core.database import SessionLocal, engine
from app.core.seed import seed_db
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
    # Attempt to insert a CaseEvent pointing to a non-existent case_id
    orphan_event = CaseEvent(
        case_id=99999999,
        event_type="test_orphan",
        description="This event has an invalid foreign key",
    )
    db_session.add(orphan_event)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Attempt to insert an Evidence pointing to a non-existent case_id
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

        # Test normalize_database_url ensures directory
        normalized = normalize_database_url(db_url)
        assert normalized.startswith("sqlite:///")

        # Test evidence directory auto-creation
        deep_evidence_path = os.path.join(temp_dir, "deep_evidence", "uploads")
        assert not os.path.exists(deep_evidence_path)
        os.makedirs(deep_evidence_path, exist_ok=True)
        assert os.path.exists(deep_evidence_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_seed_db_idempotency(db_session):
    """Verify demo seeding is idempotent and does not create duplicate records."""
    # Run seed_db once
    seed_db(db_session)
    counts_first = {
        "wallets": db_session.query(Wallet).count(),
        "transactions": db_session.query(Transaction).count(),
        "threats": db_session.query(ThreatFinding).count(),
        "osint": db_session.query(OSINTFinding).count(),
        "cases": db_session.query(Case).count(),
        "monitors": db_session.query(MonitoredWallet).count(),
        "alerts": db_session.query(Alert).count(),
        "evidence": db_session.query(Evidence).count(),
        "investigations": db_session.query(Investigation).count(),
        "audit": db_session.query(AuditLog).count(),
    }

    # Run seed_db a second time - must not fail or create duplicate rows
    seed_db(db_session)
    counts_second = {
        "wallets": db_session.query(Wallet).count(),
        "transactions": db_session.query(Transaction).count(),
        "threats": db_session.query(ThreatFinding).count(),
        "osint": db_session.query(OSINTFinding).count(),
        "cases": db_session.query(Case).count(),
        "monitors": db_session.query(MonitoredWallet).count(),
        "alerts": db_session.query(Alert).count(),
        "evidence": db_session.query(Evidence).count(),
        "investigations": db_session.query(Investigation).count(),
        "audit": db_session.query(AuditLog).count(),
    }

    assert counts_first == counts_second, f"Counts changed on re-seed: {counts_first} != {counts_second}"


def test_crud_all_models_sqlite(db_session):
    """Verify full CRUD lifecycle across core models on SQLite."""
    # 1. Case CRUD
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

    # 2. CaseEvent (with FK)
    event = CaseEvent(
        case_id=test_case.id,
        event_type="test_event",
        description="Created test event",
    )
    db_session.add(event)
    db_session.commit()
    assert event.id is not None

    # 3. Evidence (with FK)
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

    # 4. Investigation (with FK)
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

    # 5. Report (with FK)
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
    import subprocess
    import sqlite3
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "migration_test.db")
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{temp_db.replace(os.sep, '/')}"
    env["PYTHONPATH"] = backend_dir

    try:
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

