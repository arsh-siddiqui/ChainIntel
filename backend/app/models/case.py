"""Investigation case and timeline event models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow

CASE_STATUSES = ["OPEN", "UNDER_INVESTIGATION", "ON_HOLD", "RESOLVED", "CLOSED"]
CASE_PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    investigator: Mapped[str] = mapped_column(String(120), default="Investigator")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class CaseEvent(Base):
    __tablename__ = "case_events"
    __table_args__ = (Index("ix_case_events_case", "case_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    event_type: Mapped[str] = mapped_column(String(50))  # e.g. wallet_added, evidence_attached
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
