"""Live EVM provider backed by the Etherscan v2 multichain API (Ethereum, BSC)."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.services.blockchain.base import BlockchainProvider, ProviderError, unix_to_datetime

HTTP_TIMEOUT = 15.0
WEI = 1e18


class EvmProvider(BlockchainProvider):
    """Etherscan-v2 based provider; subclasses set name/blockchain/chain_id/asset."""

    name = "etherscan-v2"
    blockchain = "ethereum"
    asset = "ETH"
    chain_id = 1
    is_demo = False

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.etherscan_api_key
        self.base_url = settings.etherscan_api_url.rstrip("/")

    def _require_key(self) -> None:
        if not self.api_key:
            raise ProviderError(
                "REQUIRES_CONFIGURATION",
                f"{self.blockchain.upper()} provider is not configured: set ETHERSCAN_API_KEY in the backend environment.",
            )

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        self._require_key()
        params = {**params, "chainid": self.chain_id, "apikey": self.api_key}
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.get(self.base_url, params=params)
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"{self.blockchain} API unreachable: {exc.__class__.__name__}") from exc
        if response.status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMITED", f"{self.blockchain} API rate limit reached; retry later.")
        if response.status_code >= 400:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"{self.blockchain} API returned HTTP {response.status_code}.")
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"{self.blockchain} API returned a malformed response.") from exc

        status = str(data.get("status", data.get("jsonrpc", "")))
        message = str(data.get("message", data.get("error", "")))
        if "notok" in message.lower() or status == "-1":
            lowered = message.lower() + " " + str(data.get("result", "")).lower()
            if "rate limit" in lowered or "max calls" in lowered:
                raise ProviderError("PROVIDER_RATE_LIMITED", f"{self.blockchain} API rate limit reached; retry later.")
            if "invalid api key" in lowered:
                raise ProviderError("REQUIRES_CONFIGURATION", f"{self.blockchain} API rejected the configured key.")
            raise ProviderError("PROVIDER_UNAVAILABLE", f"{self.blockchain} API error: {message or 'unknown error'}")
        return data

    async def get_balance(self, address: str) -> dict[str, Any]:
        data = await self._get({"module": "account", "action": "balance", "address": address, "tag": "latest"})
        wei = int(data.get("result", 0) or 0)
        return {"balance": round(wei / WEI, 8), "asset": self.asset, "provider": self.name, "is_demo": False}

    @staticmethod
    def _normalize(raw: dict) -> dict[str, Any]:
        value = int(raw.get("value") or 0)
        confirmations = int(raw.get("confirmations") or 0)
        receipt_ok = str(raw.get("txreceipt_status", "1")) == "1"
        return {
            "tx_hash": raw.get("hash"),
            "blockchain": None,  # set by subclass wrapper
            "from_address": (raw.get("from") or "").lower() or None,
            "to_address": (raw.get("to") or "").lower() or None,
            "amount": round(value / WEI, 8),
            "asset": None,
            "timestamp": unix_to_datetime(raw.get("timeStamp")),
            "block_number": int(raw.get("blockNumber") or 0) or None,
            "confirmations": confirmations,
            "status": "confirmed" if confirmations > 0 and receipt_ok else "pending",
            "fee": round((int(raw.get("gasUsed") or 0) * int(raw.get("gasPrice") or 0)) / WEI, 8),
            "is_demo": False,
        }

    def _finalize(self, item: dict[str, Any]) -> dict[str, Any]:
        item["blockchain"] = self.blockchain
        item["asset"] = self.asset
        return item

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        data = await self._get(
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
        )
        raws = data.get("result") or []
        if not isinstance(raws, list):
            raise ProviderError("PROVIDER_UNAVAILABLE", f"{self.blockchain} API returned unexpected data.")
        items = []
        for raw in raws:
            item = self._normalize(raw)
            item = self._finalize(item)
            item["direction"] = "outgoing" if item["from_address"] == address.lower() else "incoming"
            items.append(item)
        return items

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        data = await self._get({"module": "proxy", "action": "eth_getTransactionByHash", "txhash": tx_hash})
        raw = data.get("result")
        if not raw:
            raise ProviderError("NOT_FOUND", f"Transaction {tx_hash} not found.")
        raw["timeStamp"] = int(raw.get("timeStamp") or "0", 16)
        raw["confirmations"] = int(raw.get("confirmations") or "0", 16) if raw.get("confirmations") else 0
        raw["value"] = int(raw.get("value") or "0", 16)
        raw["gasPrice"] = int(raw.get("gasPrice") or "0", 16)
        raw["gasUsed"] = 0
        return self._finalize(self._normalize(raw))

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        tag = hex(block_number)
        data = await self._get({"module": "proxy", "action": "eth_getBlockByNumber", "tag": tag, "boolean": "false"})
        raw = data.get("result")
        if not raw:
            raise ProviderError("NOT_FOUND", f"Block {block_number} not found.")
        return {
            "block_number": int(raw.get("number"), 16) if raw.get("number") else block_number,
            "hash": raw.get("hash"),
            "timestamp": unix_to_datetime(int(raw.get("timestamp"), 16) if raw.get("timestamp") else None),
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
