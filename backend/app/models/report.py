"""Report model: generated investigation report payloads."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    wallet_address: Mapped[str] = mapped_column(String(255))
    blockchain: Mapped[str] = mapped_column(String(50), default="unknown")
    title: Mapped[str] = mapped_column(String(255))
    mode: Mapped[str] = mapped_column(String(10), default="LIVE")
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
