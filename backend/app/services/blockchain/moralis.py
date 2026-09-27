"""Live EVM provider backed by the Moralis Web3 Data API (Ethereum, BSC).

Uses the Moralis v2.2 REST API with the ``X-API-KEY`` header:
  - balance:      GET /{address}/balance?chain=eth|bsc
  - transactions: GET /{address}?chain=eth|bsc (cursor pagination)
  - transaction:  GET /transaction/{hash}?chain=eth|bsc
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.services.blockchain.base import BlockchainProvider, ProviderError, iso_to_datetime, unix_to_datetime

HTTP_TIMEOUT = 15.0
WEI = 1e18


class MoralisProvider(BlockchainProvider):
    """Moralis based provider; subclasses set name/blockchain/chain/asset."""

    name = "moralis"
    blockchain = "ethereum"
    asset = "ETH"
    chain = "eth"
    is_demo = False

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.moralis_api_key
        self.base_url = settings.moralis_api_url.rstrip("/")

    def _require_key(self) -> None:
        if not self.api_key:
            raise ProviderError(
                "REQUIRES_CONFIGURATION",
                f"{self.blockchain.upper()} Moralis provider is not configured: set MORALIS_API_KEY in the backend environment.",
            )

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_key()
        url = f"{self.base_url}{path}"
        params = {"chain": self.chain, **(params or {})}
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.get(url, params=params, headers={"X-API-KEY": self.api_key})
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Moralis API unreachable: {exc.__class__.__name__}") from exc
        if response.status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMITED", "Moralis API rate limit reached; retry later.")
        if response.status_code == 401 or response.status_code == 403:
            raise ProviderError("REQUIRES_CONFIGURATION", "Moralis API rejected the configured key.")
        if response.status_code == 404:
            raise ProviderError("NOT_FOUND", "Resource not found on the Moralis API.")
        if response.status_code >= 400:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Moralis API returned HTTP {response.status_code}.")
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", "Moralis API returned a malformed response.") from exc

    async def get_balance(self, address: str) -> dict[str, Any]:
        data = await self._get(f"/{address}/balance")
        wei = int(data.get("balance") or 0)
        return {"balance": round(wei / WEI, 8), "asset": self.asset, "provider": self.name, "is_demo": False}

    @staticmethod
    def _normalize(raw: dict) -> dict[str, Any]:
        value = int(str(raw.get("value") or 0) or 0)
        block_number = int(raw.get("block_number") or 0) or None
        gas_price = int(str(raw.get("gas_price") or 0) or 0)
        cost = int(str(raw.get("transaction_cost") or 0) or 0)
        if not cost:
            cost = int(str(raw.get("gas_used") or raw.get("gas") or 0) or 0) * gas_price
        confirmations = int(raw.get("confirmations") or 0)
        return {
            "tx_hash": raw.get("hash"),
            "blockchain": None,
            "from_address": (raw.get("from_address") or "").lower() or None,
            "to_address": (raw.get("to_address") or "").lower() or None,
            "amount": round(value / WEI, 8),
            "asset": None,
            "timestamp": iso_to_datetime(raw.get("block_timestamp")) or unix_to_datetime(None),
            "block_number": block_number,
            "confirmations": confirmations,
            "status": "confirmed" if block_number else "pending",
            "fee": round(cost / WEI, 8),
            "is_demo": False,
        }

    def _finalize(self, item: dict[str, Any]) -> dict[str, Any]:
        item["blockchain"] = self.blockchain
        item["asset"] = self.asset
        return item

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        items: list[dict[str, Any]] = []
        cursor: str | None = None
        while len(items) < limit:
            params: dict[str, Any] = {"limit": min(100, limit - len(items))}
            if cursor:
                params["cursor"] = cursor
            data = await self._get(f"/{address}", params)
            raws = data.get("result") or []
            for raw in raws:
                item = self._finalize(self._normalize(raw))
                item["direction"] = "outgoing" if item["from_address"] == address.lower() else "incoming"
                items.append(item)
            cursor = data.get("cursor") or None
            if not cursor or not raws:
                break
        return items

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        raw = await self._get(f"/transaction/{tx_hash}")
        if not raw or not raw.get("hash"):
            raise ProviderError("NOT_FOUND", f"Transaction {tx_hash} not found.")
        return self._finalize(self._normalize(raw))

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        raw = await self._get(f"/block/{block_number}")
        if not raw:
            raise ProviderError("NOT_FOUND", f"Block {block_number} not found.")
        return {
            "block_number": int(raw.get("block_number") or block_number),
            "hash": raw.get("block_hash") or raw.get("hash"),
            "timestamp": iso_to_datetime(raw.get("block_timestamp") or raw.get("timestamp")),
            "tx_count": len(raw.get("transactions") or []),
            "is_demo": False,
        }

    async def get_address_activity(self, address: str) -> dict[str, Any]:
        txs = await self.get_transactions(address, limit=100)
        timestamps = [t["timestamp"] for t in txs if t["timestamp"]]
        return {
            "first_seen": min(timestamps) if timestamps else None,
            "last_seen": max(timestamps) if timestamps else None,
            "tx_count": len(txs),
            "is_demo": False,
        }


class MoralisEthereumProvider(MoralisProvider):
    name = "moralis (ethereum)"
    blockchain = "ethereum"
    asset = "ETH"
    chain = "eth"


class MoralisBSCProvider(MoralisProvider):
    name = "moralis (bsc)"
    blockchain = "bsc"
    asset = "BNB"
    chain = "bsc"
