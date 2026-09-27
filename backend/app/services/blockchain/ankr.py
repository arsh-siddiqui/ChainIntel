"""Live EVM provider backed by the Ankr Advanced API (Ethereum, BSC).

Verified against the real API (2026-09):
  - ``ankr_getAccountBalance``      → ``result.assets[]`` with tokenType/tokenDecimals/
                                      balanceRawInteger (decimal OR hex string).
  - ``ankr_getTransactionsByAddress`` → ``result.transactions[]`` in ETH JSON-RPC style
                                      (hex quantities, ``from``/``to``, ``value`` in wei hex).
  - ``ankr_getTransactionByHash``   → same tx shape wrapped in ``result.transaction``.
  - Block info via standard ``eth_getBlockByNumber`` JSON-RPC on rpc.ankr.com.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.services.blockchain.base import BlockchainProvider, ProviderError, iso_to_datetime, unix_to_datetime

HTTP_TIMEOUT = 15.0


def _int_from_raw(value: Any) -> int:
    """Parse ints from decimal strings, hex strings ("0x.."), or plain ints."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip()
    try:
        return int(text, 16) if text.lower().startswith("0x") else int(text)
    except ValueError:
        return 0


class AnkrProvider(BlockchainProvider):
    """Ankr Advanced API provider; subclasses set name/blockchain/ankr_chain/asset."""

    name = "ankr"
    blockchain = "ethereum"
    asset = "ETH"
    ankr_chain = "eth"
    is_demo = False

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.ankr_api_key
        self.base_url = settings.ankr_api_url.rstrip("/")
        host = self.base_url.rsplit("/multichain", 1)[0] or "https://rpc.ankr.com"
        self.rpc_url = f"{host}/{self.ankr_chain}"

    def _require_key(self) -> None:
        if not self.api_key:
            raise ProviderError(
                "REQUIRES_CONFIGURATION",
                f"{self.blockchain.upper()} Ankr provider is not configured: set ANKR_API_KEY in the backend environment.",
            )

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def _rpc(self, url: str, method: str, params: dict[str, Any] | list[Any]) -> dict[str, Any]:
        self._require_key()
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(url, json=payload, headers=self._headers())
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Ankr API unreachable: {exc.__class__.__name__}") from exc
        if response.status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMITED", "Ankr API rate limit reached; retry later.")
        if response.status_code in (401, 403):
            raise ProviderError("REQUIRES_CONFIGURATION", "Ankr API rejected the configured key.")
        if response.status_code >= 400:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Ankr API returned HTTP {response.status_code}.")
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", "Ankr API returned a malformed response.") from exc
        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            message = error.get("message", "unknown error") if isinstance(error, dict) else str(error)
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Ankr API error: {message}")
        return data

    async def _advanced(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._rpc(self.base_url, method, params)

    async def get_balance(self, address: str) -> dict[str, Any]:
        data = await self._advanced(
            "ankr_getAccountBalance",
            {"blockchain": [self.ankr_chain], "walletAddress": address, "onlyWhitelisted": False},
        )
        assets = ((data.get("result") or {}).get("assets")) or []
        native = next((a for a in assets if str(a.get("tokenType", "")).upper() == "NATIVE"), None) or next(
            (a for a in assets if not a.get("contractAddress")), None
        )
        if native is None:
            return {"balance": 0.0, "asset": self.asset, "provider": self.name, "is_demo": False}
        decimals = _int_from_raw(native.get("tokenDecimals") or native.get("valueDecimals")) or 18
        raw = native.get("balanceRawInteger")
        if raw:
            balance = _int_from_raw(raw) / (10**decimals)
        else:
            try:
                balance = float(native.get("balance") or 0)
            except (TypeError, ValueError):
                balance = 0.0
        return {"balance": round(balance, 8), "asset": self.asset, "provider": self.name, "is_demo": False}

    @staticmethod
    def _normalize(raw: dict) -> dict[str, Any]:
        """Normalize a transaction in either observed shape (JSON-RPC hex or camelCase)."""
        decimals = _int_from_raw(raw.get("valueDecimals") or raw.get("tokenDecimals")) or 18
        amount = _int_from_raw(raw.get("value")) / (10**decimals)
        block_number = _int_from_raw(raw.get("blockNumber")) or None

        # Status: hex ("0x1"), enum ("SUCCESS"), or empty for pending.
        status_raw = str(raw.get("status") or "").upper()
        if status_raw in ("0X1", "SUCCESS", "1"):
            status = "confirmed"
        elif status_raw in ("0X0", "FAILED", "0"):
            status = "failed"
        else:
            status = "pending" if not block_number else "confirmed"

        timestamp = iso_to_datetime(raw.get("blockTimestamp")) or unix_to_datetime(
            _int_from_raw(raw.get("timestamp")) or None
        )

        try:
            fee = float(raw.get("fee") or 0)
        except (TypeError, ValueError):
            fee = 0.0
        if not fee and raw.get("gasUsed") is not None and raw.get("gasPrice") is not None:
            fee = _int_from_raw(raw.get("gasUsed")) * _int_from_raw(raw.get("gasPrice")) / (10**18)

        return {
            "tx_hash": raw.get("hash"),
            "blockchain": None,
            "from_address": (raw.get("fromAddress") or raw.get("from") or "").lower() or None,
            "to_address": (raw.get("toAddress") or raw.get("to") or "").lower() or None,
            "amount": round(amount, 8),
            "asset": None,
            "timestamp": timestamp,
            "block_number": block_number,
            "confirmations": _int_from_raw(raw.get("confirmations")),
            "status": status,
            "fee": round(fee, 8),
            "is_demo": False,
        }

    def _finalize(self, item: dict[str, Any]) -> dict[str, Any]:
        item["blockchain"] = self.blockchain
        item["asset"] = self.asset
        return item

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        data = await self._advanced(
            "ankr_getTransactionsByAddress",
            {
                "blockchain": [self.ankr_chain],
                "address": address,
                "pageSize": min(limit, 100),
                "descOrder": True,
            },
        )
        raws = ((data.get("result") or {}).get("transactions")) or []
        items = []
        for raw in raws:
            item = self._finalize(self._normalize(raw))
            item["direction"] = "outgoing" if item["from_address"] == address.lower() else "incoming"
            items.append(item)
        return items

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        data = await self._advanced(
            "ankr_getTransactionByHash",
            {"transactionHash": tx_hash, "blockchain": [self.ankr_chain]},
        )
        raw = (data.get("result") or {}).get("transaction")
        if not raw:
            raise ProviderError("NOT_FOUND", f"Transaction {tx_hash} not found.")
        return self._finalize(self._normalize(raw))

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        data = await self._rpc(
            self.rpc_url,
            "eth_getBlockByNumber",
            [hex(block_number), False],
        )
        raw = data.get("result")
        if not raw:
            raise ProviderError("NOT_FOUND", f"Block {block_number} not found.")
        return {
            "block_number": _int_from_raw(raw.get("number")) or block_number,
            "hash": raw.get("hash"),
            "timestamp": unix_to_datetime(_int_from_raw(raw.get("timestamp"))),
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


class AnkrEthereumProvider(AnkrProvider):
    name = "ankr (ethereum)"
    blockchain = "ethereum"
    asset = "ETH"
    ankr_chain = "eth"


class AnkrBSCProvider(AnkrProvider):
    name = "ankr (bsc)"
    blockchain = "bsc"
    asset = "BNB"
    ankr_chain = "bsc"
