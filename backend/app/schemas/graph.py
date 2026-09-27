"""Graph request schemas."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TraceRequest(BaseModel):
    wallet_address: str = Field(min_length=4, max_length=255)
    direction: Literal["outgoing", "incoming"] = "outgoing"
    target_address: Optional[str] = Field(default=None, max_length=255)
    max_hops: int = Field(default=3, ge=1, le=7)
