"""Alert and monitoring schemas."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class MonitorCreate(BaseModel):
    wallet_address: str = Field(min_length=4, max_length=255)
    blockchain: str = Field(default="bitcoin", max_length=50)
    label: Optional[str] = Field(default=None, max_length=255)
    rules: dict[str, Any] = Field(default_factory=dict)


class MonitorUpdate(BaseModel):
    status: Literal["ACTIVE", "PAUSED"]


class AlertUpdate(BaseModel):
    status: Literal["NEW", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED"]
