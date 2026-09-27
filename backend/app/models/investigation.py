"""Investigation model: one wallet analysis run with its result payload."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow


class Investigation(Base):
    __tablename__ = "investigations"
    __table_args__ = (Index("ix_investigations_address", "wallet_address"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    wallet_address: Mapped[str] = mapped_column(String(255))
    blockchain: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED")  # COMPLETED | IN_PROGRESS | ARCHIVED
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    investigator: Mapped[str] = mapped_column(String(120), default="Investigator")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
