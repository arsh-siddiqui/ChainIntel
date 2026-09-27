"""Live Bitcoin provider backed by the public mempool.space REST API (no API key)."""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.config import settings
from app.services.blockchain.base import BlockchainProvider, ProviderError, unix_to_datetime

HTTP_TIMEOUT = 15.0


class BitcoinProvider(BlockchainProvider):
    name = "mempool.space"
    blockchain = "bitcoin"
    asset = "BTC"
    is_demo = False

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.mempool_api_url).rstrip("/")

    async def _get(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Bitcoin API unreachable: {exc.__class__.__name__}") from exc
        if response.status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMITED", "Bitcoin API rate limit reached; retry later.")
        if response.status_code >= 400:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Bitcoin API returned HTTP {response.status_code}.")
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", "Bitcoin API returned a malformed response.") from exc

    async def _tip_height(self) -> int:
        return int(await self._get("/blocks/tip/height"))

    async def get_balance(self, address: str) -> dict[str, Any]:
        data = await self._get(f"/address/{address}")
        stats = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})
        satoshis = stats.get("funded_txo_sum", 0) - stats.get("spent_txo_sum", 0)
        pending = mempool.get("funded_txo_sum", 0) - mempool.get("spent_txo_sum", 0)
        return {
            "balance": round(satoshis / 1e8, 8),
            "pending_balance": round(pending / 1e8, 8),
            "asset": self.asset,
            "provider": self.name,
            "is_demo": False,
        }

    async def _normalize(self, raw: dict, tip: int | None, address: str | None = None) -> dict[str, Any] | None:
        txid = raw.get("txid")
        if not txid:
            return None
        status = raw.get("status", {})
        confirmed = bool(status.get("confirmed"))
        height = status.get("block_height")
        confirmations = (tip - height + 1) if (confirmed and tip and height) else 0

        vins = raw.get("vin", []) or []
        vouts = raw.get("vout", []) or []

        def addr_of_vout(vout: dict) -> str | None:
            return ((vout.get("scriptpubkey_address") or "") or None)

        def addr_of_vin(vin: dict) -> str | None:
            prevout = vin.get("prevout") or {}
            return prevout.get("scriptpubkey_address")

        received_outputs = [(addr_of_vout(v), (v.get("value") or 0) / 1e8) for v in vouts]
        input_addrs = [a for a in (addr_of_vin(v) for v in vins) if a]

        # Find outputs going back to the inputs (change) and exclude them for "sent" amount.
        change = sum(amount for a, amount in received_outputs if a and a in set(input_addrs))
        total_in = sum((v.get("value") or 0) for v in vins) / 1e8

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
            credited = sum(amount for a, amount in received_outputs if a == address)
            amount = credited
            from_address = input_addrs[0] if input_addrs else None
            to_address = address
        else:
            # No address context (single-tx lookup): report raw endpoints without a direction.
            direction = "unknown"
            amount = max((amount for _, amount in received_outputs if amount > 0), default=0)
            from_address = input_addrs[0] if input_addrs else None
            outputs = [(a, amount) for a, amount in received_outputs if a and a != from_address and amount > 0]
            to_address = max(outputs, key=lambda x: x[1])[0] if outputs else None

        return {
            "tx_hash": txid,
            "blockchain": self.blockchain,
            "from_address": from_address,
            "to_address": to_address,
            "amount": round(amount, 8),
            "asset": self.asset,
            "timestamp": unix_to_datetime(status.get("block_time")),
            "block_number": height,
            "confirmations": confirmations,
            "status": "confirmed" if confirmed else "pending",
            "fee": round((raw.get("fee") or 0) / 1e8, 8),
            "is_demo": False,
            "direction": direction,
        }

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        tip = await self._tip_height()
        raw_txs: list[dict] = []
        first_page = await self._get(f"/address/{address}/txs")
        raw_txs.extend(first_page)
        last_txid = first_page[-1]["txid"] if first_page else None
        while len(raw_txs) < limit and last_txid:
            page = await self._get(f"/address/{address}/txs/chain/{last_txid}")
            if not page:
                break
            raw_txs.extend(page)
            last_txid = page[-1]["txid"]
            await asyncio.sleep(0.15)  # polite pagination

        normalized: list[dict] = []
        seen: set[str] = set()
        for raw in raw_txs:
            if raw.get("txid") in seen:
                continue
            seen.add(raw.get("txid"))
            item = await self._normalize(raw, tip, address)
            if item and item["amount"] > 0:
                normalized.append(item)
        return normalized[:limit]

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        raw = await self._get(f"/tx/{tx_hash}")
        tip = await self._tip_height()
        # Normalize against the first input/output addresses.
        raw_copy = dict(raw)
        item = await self._normalize(raw_copy, tip, address=None)
        if item is None:
            raise ProviderError("NOT_FOUND", f"Transaction {tx_hash} not found.")
        return item

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        block_hash = await self._get(f"/block-height/{block_number}")
        if not isinstance(block_hash, str):
            raise ProviderError("NOT_FOUND", f"Block {block_number} not found.")
        block = await self._get(f"/block/{block_hash}")
        return {
            "block_number": block.get("height"),
            "hash": block.get("id"),
            "timestamp": unix_to_datetime(block.get("timestamp")),
            "tx_count": block.get("tx_count"),
            "is_demo": False,
        }

    async def get_address_activity(self, address: str) -> dict[str, Any]:
        data = await self._get(f"/address/{address}")
        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})
        tx_count = chain.get("tx_count", 0) + mempool.get("tx_count", 0)
        first_seen = last_seen = None
        if tx_count:
            txs = await self.get_transactions(address, limit=1)
            if txs:
                last_seen = txs[0]["timestamp"]
            first_seen = unix_to_datetime(chain.get("first_seen") or None) or last_seen
        return {"first_seen": first_seen, "last_seen": last_seen, "tx_count": tx_count, "is_demo": False}
