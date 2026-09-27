"""Deterministic fake blockchain provider for hermetic tests.

Provides canned Bitcoin/Ethereum-shaped data so tests exercise the full
pipeline without network access. Never used in production code paths.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.blockchain.base import BlockchainProvider, ProviderError

_NOW = datetime(2026, 1, 15, 12, 0, 0)


def _ts(hours_ago: int) -> datetime:
    from datetime import timedelta

    return _NOW - timedelta(hours=hours_ago)


BTC_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # valid P2PKH
CP1 = "1HdS1CMasR6XMN4F5L8uLqEtduUV2uuD6C"  # valid Base58Check counterparty
CP2 = "1DV391rtxMcjofZWfmQGaDpcEQDxmRF8sd"  # valid Base58Check counterparty
ETH_ADDRESS = "0x" + "ab" * 20

TXS = [
    {
        "tx_hash": "fake-tx-out-1",
        "from_address": BTC_ADDRESS,
        "to_address": CP1,
        "amount": 0.75,
        "asset": "BTC",
        "timestamp": _ts(1),
        "block_number": 800001,
        "confirmations": 6,
        "status": "confirmed",
        "fee": 0.0001,
        "is_demo": False,
    },
    {
        "tx_hash": "fake-tx-in-1",
        "from_address": CP1,
        "to_address": BTC_ADDRESS,
        "amount": 1.25,
        "asset": "BTC",
        "timestamp": _ts(5),
        "block_number": 800000,
        "confirmations": 12,
        "status": "confirmed",
        "fee": 0.0002,
        "is_demo": False,
    },
    {
        "tx_hash": "fake-tx-in-2",
        "from_address": CP2,
        "to_address": BTC_ADDRESS,
        "amount": 0.5,
        "asset": "BTC",
        "timestamp": _ts(30),
        "block_number": 799990,
        "confirmations": 50,
        "status": "confirmed",
        "fee": 0.0001,
        "is_demo": False,
    },
]


class FakeProvider(BlockchainProvider):
    name = "fake-provider"
    blockchain = "bitcoin"
    asset = "BTC"
    is_demo = False

    def __init__(self, blockchain: str = "bitcoin", asset: str = "BTC"):
        self.blockchain = blockchain
        self.asset = asset

    async def get_balance(self, address: str) -> dict[str, Any]:
        incoming = sum(t["amount"] for t in TXS if t["to_address"] == address)
        outgoing = sum(t["amount"] for t in TXS if t["from_address"] == address)
        return {"balance": round(incoming - outgoing, 8), "asset": self.asset, "provider": self.name, "is_demo": False}

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        txs = [t for t in TXS if t["from_address"] == address or t["to_address"] == address]
        return [dict(t) for t in txs[: max(1, min(limit, 200))]]

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        for t in TXS:
            if t["tx_hash"] == tx_hash:
                return dict(t)
        raise ProviderError("NOT_FOUND", f"Transaction {tx_hash} not found.")

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        return {"block_number": block_number, "hash": f"fake-block-{block_number}", "timestamp": _ts(1), "tx_count": 1}

    async def get_address_activity(self, address: str) -> dict[str, Any]:
        txs = [t for t in TXS if t["from_address"] == address or t["to_address"] == address]
        timestamps = [t["timestamp"] for t in txs]
        return {
            "first_seen": min(timestamps) if timestamps else None,
            "last_seen": max(timestamps) if timestamps else None,
            "tx_count": len(txs),
        }


def install_fake_provider(monkeypatch, blockchain: str | None = None):
    """Patch provider_for_address/get_provider to return the FakeProvider.

    Patches every import site (factory, wallet_analysis, monitoring) because
    these names are bound at module import time.
    """

    from app.services import monitoring as monitoring_module
    from app.services import wallet_analysis as wallet_analysis_module
    from app.services.blockchain import factory

    provider = FakeProvider(blockchain or "bitcoin")

    def fake_get_provider(chain: str):
        if blockchain and chain != blockchain:
            raise ProviderError("UNKNOWN_BLOCKCHAIN", f"Unsupported blockchain '{chain}'.")
        return provider

    def fake_provider_for_address(address: str, requested: str = "auto"):
        from app.utils.address_validation import detect_blockchain

        detection = detect_blockchain(address, requested)
        if not detection["valid"]:
            from app.core.envelope import AppError

            raise AppError(400, "INVALID_WALLET", detection["reason"], {"detection": detection})
        return provider, detection

    monkeypatch.setattr(factory, "get_provider", fake_get_provider)
    monkeypatch.setattr(factory, "provider_for_address", fake_provider_for_address)
    monkeypatch.setattr(wallet_analysis_module, "provider_for_address", fake_provider_for_address, raising=False)
    # monitoring.py imports get_provider lazily inside _poll_live_wallet; patch it too if present.
    monkeypatch.setattr(monitoring_module, "get_provider", fake_get_provider, raising=False)
    return provider
