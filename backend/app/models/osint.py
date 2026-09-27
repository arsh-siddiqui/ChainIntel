"""OSINT finding model (public providers, restricted-source records, analyst notes)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow

OSINT_STATUSES = ["FOUND", "NOT_FOUND", "UNAVAILABLE", "ERROR", "REQUIRES_CONFIGURATION"]
RESTRICTED_RECORD_TYPES = ["VERIFIED_SOURCE", "IMPORTED_INTELLIGENCE", "ANALYST_NOTE", "UNAVAILABLE"]


class OSINTFinding(Base):
    __tablename__ = "osint_findings"
    __table_args__ = (Index("ix_osint_address", "wallet_address"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(255))
    source_category: Mapped[str] = mapped_column(String(30), default="public")  # public | restricted | analyst
    record_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)  # restricted records only
    finding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="NOT_FOUND")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reference_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
