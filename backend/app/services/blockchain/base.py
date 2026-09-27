"""Abstract blockchain provider interface.

Every provider returns NORMALIZED transaction dicts:
{
  tx_hash, blockchain, from_address, to_address, amount, asset,
  timestamp (datetime UTC naive), block_number, confirmations,
  status ("confirmed"|"pending"), fee, is_demo
}
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.utils.address_validation import validate_address


class ProviderError(Exception):
    """Raised when a provider cannot serve a request.

    Codes:
      PROVIDER_UNAVAILABLE     - network/API failure; never fake data on top of this
      REQUIRES_CONFIGURATION   - API key missing
      PROVIDER_RATE_LIMITED    - upstream rate limit
      NOT_FOUND                - resource does not exist upstream
      UNKNOWN_BLOCKCHAIN       - unsupported chain requested
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class BlockchainProvider(ABC):
    name: str = "abstract"
    blockchain: str = "unknown"
    asset: str = "BTC"
    is_demo: bool = False

    @abstractmethod
    async def get_balance(self, address: str) -> dict[str, Any]:
        """Return {"balance": float, "asset": str, "provider": name}."""

    @abstractmethod
    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        """Return normalized transactions touching the address (newest first)."""

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        """Return a single normalized transaction."""

    @abstractmethod
    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        """Return {"block_number", "hash", "timestamp", "tx_count"}."""

    @abstractmethod
    async def get_address_activity(self, address: str) -> dict[str, Any]:
        """Return {"first_seen": datetime|None, "last_seen": datetime|None, "tx_count": int}."""

    def validate_address(self, address: str) -> dict:
        return validate_address(address)


def unix_to_datetime(seconds: int | float | None) -> datetime | None:
    if not seconds:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(int(seconds), tz=timezone.utc).replace(tzinfo=None)


def iso_to_datetime(value: str | None) -> datetime | None:
    """Parse ISO-8601 timestamps (e.g. 2021-04-02T10:22:04.000Z) to naive UTC."""
    if not value:
        return None
    from datetime import datetime, timezone

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed
