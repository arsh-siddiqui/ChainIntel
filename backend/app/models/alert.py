"""Alert and monitored-wallet models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.datetime import utcnow

ALERT_STATUSES = ["NEW", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED"]
ALERT_SEVERITIES = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_wallet", "wallet_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String(255))
    rule: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    transaction_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(20), default="NEW")
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MonitoredWallet(Base):
    __tablename__ = "monitored_wallets"
    __table_args__ = (UniqueConstraint("wallet_address", name="uq_monitored_address"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String(255))
    blockchain: Mapped[str] = mapped_column(String(50), default="bitcoin")
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rules: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE | PAUSED
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
