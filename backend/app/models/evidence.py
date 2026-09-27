"""Evidence model: files, notes and captured artifacts with SHA-256 integrity."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow

EVIDENCE_TYPES = [
    "Screenshot",
    "Transaction Hash",
    "Wallet Address",
    "API Response",
    "OSINT Result",
    "Document",
    "Analyst Note",
    "Graph Snapshot",
]


class Evidence(Base):
    __tablename__ = "evidence"
    __table_args__ = (Index("ix_evidence_case", "case_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
