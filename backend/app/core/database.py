"""Database engine, session management and model base for SQLite."""
from __future__ import annotations

import os
import sqlite3
from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import ensure_db_directory, settings
from app.core.logging import get_logger

logger = get_logger("database")


# Enforce foreign key constraints on all SQLite connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"connect_args": {"check_same_thread": False}}


db_url = settings.effective_database_url
ensure_db_directory(db_url)

engine = create_engine(db_url, **_engine_kwargs(db_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> dict[str, str]:
    """Check database connection and return status details safely without passwords."""
    dialect_name = engine.dialect.name
    sanitized_url = settings.sanitized_database_url
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection active (dialect=%s, url=%s)", dialect_name, sanitized_url)
        return {"status": "connected", "dialect": dialect_name, "url": sanitized_url}
    except Exception as exc:
        logger.error("Database connection failure (url=%s): %s", sanitized_url, exc)
        return {"status": "failed", "dialect": dialect_name, "url": sanitized_url, "error": str(exc)}


def init_db() -> None:
    from app import models  # noqa: F401 - register all models on the metadata
    from app.core.seed import seed_db

    ensure_db_directory(settings.effective_database_url)
    check_db_connection()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
