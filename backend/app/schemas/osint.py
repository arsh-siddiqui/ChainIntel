"""OSINT schemas."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RestrictedSourceCreate(BaseModel):
    wallet_address: str = Field(min_length=4, max_length=255)
    source: str = Field(min_length=1, max_length=255)
    record_type: Literal["VERIFIED_SOURCE", "IMPORTED_INTELLIGENCE", "ANALYST_NOTE", "UNAVAILABLE"] = "ANALYST_NOTE"
    finding: str = Field(min_length=1, max_length=4000)
    reference_url: Optional[str] = Field(default=None, max_length=512)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: Optional[str] = None
