"""Report schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    wallet_address: Optional[str] = Field(default=None, min_length=4, max_length=255)
    case_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=255)
