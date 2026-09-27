"""Case management schemas."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=8000)
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    status: Literal["OPEN", "UNDER_INVESTIGATION", "ON_HOLD", "RESOLVED", "CLOSED"] = "OPEN"
    investigator: str = Field(default="Investigator", max_length=120)


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=8000)
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    status: Optional[Literal["OPEN", "UNDER_INVESTIGATION", "ON_HOLD", "RESOLVED", "CLOSED"]] = None


class CaseInvestigationLink(BaseModel):
    wallet_address: str = Field(min_length=4, max_length=255)


class CaseNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=8000)
