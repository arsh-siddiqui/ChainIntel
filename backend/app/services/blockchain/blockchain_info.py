"""Bitcoin fallback provider backed by the public blockchain.info REST API.

Works without an API key (public endpoints, aggressive rate limits).
An optional ``api_code`` (BLOCKCHAIN_API_KEY) raises the rate limit.
Serves as the secondary provider behind mempool.space.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.services.blockchain.base import BlockchainProvider, ProviderError, unix_to_datetime

HTTP_TIMEOUT = 15.0


class BlockchainInfoProvider(BlockchainProvider):
    name = "blockchain.info"
    blockchain = "bitcoin"
    asset = "BTC"
    is_demo = False

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.bitcoin_api_url).rstrip("/")
        self.api_key = api_key or settings.blockchain_api_key

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        params = {"cors": "true", **(params or {})}
        if self.api_key:
            params["api_code"] = self.api_key
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"blockchain.info API unreachable: {exc.__class__.__name__}") from exc
        if response.status_code == 404:
            raise ProviderError("NOT_FOUND", f"blockchain.info resource '{path}' not found.")
        if response.status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMITED", "blockchain.info API rate limit reached; retry later.")
        if response.status_code >= 400:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"blockchain.info API returned HTTP {response.status_code}.")
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", "blockchain.info API returned a malformed response.") from exc

    async def get_balance(self, address: str) -> dict[str, Any]:
        try:
            data = await self._get(f"/rawaddr/{address}")
        except ProviderError as exc:
            if exc.code == "NOT_FOUND":
                return {
                    "balance": 0.0,
                    "asset": self.asset,
                    "provider": self.name,
                    "is_demo": False,
                }
            raise
        return {
            "balance": round((data.get("final_balance") or 0) / 1e8, 8),
            "asset": self.asset,
            "provider": self.name,
            "is_demo": False,
        }

    @staticmethod
    def _normalize(raw: dict, address: str | None = None) -> dict[str, Any] | None:
        tx_hash = raw.get("hash")
        if not tx_hash:
            return None
        vins = raw.get("inputs") or []
        vouts = raw.get("out") or []

        def addr_of_vout(vout: dict) -> str | None:
            return vout.get("addr")

        def addr_of_vin(vin: dict) -> str | None:
            prevout = vin.get("prev_out") or {}
            return prevout.get("addr")

        received_outputs = [(addr_of_vout(v), (v.get("value") or 0) / 1e8) for v in vouts]
        input_addrs = [a for a in (addr_of_vin(v) for v in vins) if a]
        total_in = sum((v.get("prev_out") or {}).get("value") or 0 for v in vins) / 1e8
        change = sum(amount for a, amount in received_outputs if a and a in set(input_addrs))

        if address is not None and address in set(input_addrs):
            direction = "outgoing"
            from_address = address
            sent_net = max(total_in - change, 0)
            recipients = [(a, amount) for a, amount in received_outputs if a and a != address and amount > 0]
            if recipients:
                to_address, amount = max(recipients, key=lambda x: x[1])
            else:
                to_address, amount = None, round(sent_net, 8)
        elif address is not None:
            direction = "incoming"
            amount = sum(amount for a, amount in received_outputs if a == address)
            from_address = input_addrs[0] if input_addrs else None
            to_address = address
        else:
            direction = "unknown"
            amount = max((amount for _, amount in received_outputs if amount > 0), default=0)
            from_address = input_addrs[0] if input_addrs else None
            outputs = [(a, amount) for a, amount in received_outputs if a and a != from_address and amount > 0]
            to_address = max(outputs, key=lambda x: x[1])[0] if outputs else None

        height = raw.get("block_height")
        return {
            "tx_hash": tx_hash,
            "blockchain": "bitcoin",
            "from_address": from_address,
            "to_address": to_address,
            "amount": round(amount, 8),
            "asset": "BTC",
            "timestamp": unix_to_datetime(raw.get("time")),
            "block_number": height,
            "confirmations": 0,
            "status": "confirmed" if height else "pending",
            "fee": round((raw.get("fee") or 0) / 1e8, 8),
            "is_demo": False,
            "direction": direction,
        }

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        try:
            data = await self._get(f"/rawaddr/{address}")
        except ProviderError as exc:
            if exc.code == "NOT_FOUND":
                return []
            raise
        raws = data.get("txs") or []
        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in raws:
            if raw.get("hash") in seen:
                continue
            seen.add(raw.get("hash"))
            item = self._normalize(raw, address)
            if item and item["amount"] > 0:
                items.append(item)
        return items[:limit]

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        raw = await self._get(f"/rawtx/{tx_hash}")
        item = self._normalize(raw, address=None)
        if item is None:
            raise ProviderError("NOT_FOUND", f"Transaction {tx_hash} not found.")
        return item

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        raw = await self._get(f"/block-height/{block_number}")
        if not raw or not isinstance(raw, dict) or not raw.get("hash"):
            raise ProviderError("NOT_FOUND", f"Block {block_number} not found.")
        return {
            "block_number": raw.get("height") or block_number,
            "hash": raw.get("hash"),
            "timestamp": unix_to_datetime(raw.get("time")),
            "tx_count": raw.get("n_tx"),
            "is_demo": False,
        }

    async def get_address_activity(self, address: str) -> dict[str, Any]:
        try:
            data = await self._get(f"/rawaddr/{address}")
        except ProviderError as exc:
            if exc.code == "NOT_FOUND":
                return {"first_seen": None, "last_seen": None, "tx_count": 0, "is_demo": False}
            raise
        txs = await self.get_transactions(address, limit=1)
        timestamps = [t["time"] for t in data.get("txs") or [] if t.get("time")]
        return {
            "first_seen": unix_to_datetime(min(timestamps)) if timestamps else None,
            "last_seen": txs[0]["timestamp"] if txs else None,
            "tx_count": int(data.get("n_tx") or 0),
            "is_demo": False,
        }
