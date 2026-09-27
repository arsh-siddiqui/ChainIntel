"""Threat intelligence record model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow

THREAT_CATEGORIES = [
    "Ransomware",
    "Scam",
    "Phishing",
    "Blacklist",
    "Fraud",
    "Exploit",
    "Suspicious Service",
    "Unknown",
]


class ThreatFinding(Base):
    __tablename__ = "threat_findings"
    __table_args__ = (
        UniqueConstraint("wallet_address", "source", "category", "label", name="uq_threat_record"),
        Index("ix_threats_category", "category"),
        Index("ix_threats_source", "source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String(255))
    blockchain: Mapped[str] = mapped_column(String(50), default="unknown")
    category: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(255))
    reference_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="IMPORTED")  # IMPORTED | VERIFIED
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
