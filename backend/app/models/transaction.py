"""Normalized blockchain transaction model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("tx_hash", "from_address", "to_address", name="uq_tx_hash_parties"),
        Index("ix_transactions_from", "from_address"),
        Index("ix_transactions_to", "to_address"),
        Index("ix_transactions_chain_ts", "blockchain", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tx_hash: Mapped[str] = mapped_column(String(255), index=True)
    blockchain: Mapped[str] = mapped_column(String(50), index=True)
    from_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    asset: Mapped[str] = mapped_column(String(20), default="BTC")
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
