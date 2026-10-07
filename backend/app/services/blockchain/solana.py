"""Solana (SOL) blockchain provider using official public JSON-RPC nodes."""
from __future__ import annotations

from typing import Any
import httpx

from app.services.blockchain.base import BlockchainProvider, ProviderError, unix_to_datetime

HTTP_TIMEOUT = 12.0
LAMPORTS_PER_SOL = 1_000_000_000


class SolanaProvider(BlockchainProvider):
    """Solana Mainnet public JSON-RPC provider (keyless)."""

    name = "solana-rpc"
    blockchain = "solana"
    asset = "SOL"
    is_demo = False

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url

    async def _rpc_call(self, method: str, params: list[Any]) -> Any:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(self.rpc_url, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Solana RPC unreachable: {exc.__class__.__name__}") from exc
        if response.status_code >= 400:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Solana RPC returned HTTP {response.status_code}.")
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE", "Solana RPC returned invalid JSON.") from exc
        if "error" in data:
            raise ProviderError("PROVIDER_UNAVAILABLE", f"Solana RPC error: {data['error'].get('message', 'unknown')}")
        return data.get("result")

    async def get_balance(self, address: str) -> dict[str, Any]:
        res = await self._rpc_call("getBalance", [address])
        value = res.get("value", 0) if isinstance(res, dict) else 0
        return {"balance": round(value / LAMPORTS_PER_SOL, 6), "asset": self.asset, "provider": self.name, "is_demo": False}

    async def get_transactions(self, address: str, limit: int = 50) -> list[dict[str, Any]]:
        sigs = await self._rpc_call("getSignaturesForAddress", [address, {"limit": min(limit, 50)}])
        if not isinstance(sigs, list):
            return []

        txs = []
        for s in sigs:
            tx_hash = s.get("signature")
            block_time = s.get("blockTime")
            err = s.get("err")
            txs.append({
                "tx_hash": tx_hash,
                "blockchain": self.blockchain,
                "from_address": address,
                "to_address": None,
                "amount": 0.0,
                "asset": self.asset,
                "timestamp": unix_to_datetime(block_time) if block_time else None,
                "block_number": s.get("slot"),
                "confirmations": 100,
                "status": "failed" if err else "confirmed",
                "fee": 0.000005,
                "is_demo": False,
            })
        return txs
