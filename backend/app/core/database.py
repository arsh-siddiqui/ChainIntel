"""Database engine, session management and model base."""
from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

os.makedirs("data", exist_ok=True)


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


db_url = settings.effective_database_url
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


def init_db() -> None:
    from app import models  # noqa: F401 - register all models on the metadata
    from app.core.seed import seed_db

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()

