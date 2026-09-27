"""Threat intelligence schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ThreatRecordIn(BaseModel):
    address: str = Field(min_length=4, max_length=255)
    blockchain: str = Field(default="unknown", max_length=50)
    label: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=50)
    source: str = Field(min_length=1, max_length=255)
    reference_url: Optional[str] = Field(default=None, max_length=512)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    notes: Optional[str] = None


class ThreatImportResult(BaseModel):
    received: int
    valid: int
    invalid: int
    duplicates: int
    inserted: int
    updated: int
    errors: list[str] = []
