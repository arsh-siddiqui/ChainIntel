"""Wallet request schemas."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class InvestigateRequest(BaseModel):
    address: str = Field(min_length=4, max_length=255)
    blockchain: Literal["auto", "bitcoin", "ethereum", "bsc"] = "auto"

    @field_validator("address")
    @classmethod
    def strip_address(cls, value: str) -> str:
        return value.strip()


class WalletNotesUpdate(BaseModel):
    notes: str = Field(default="", max_length=20000)
