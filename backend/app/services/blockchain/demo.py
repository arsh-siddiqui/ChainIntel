"""Demo blockchain provider for DEMO MODE.

Generates realistic mock blockchain data locally without network calls.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

from app.services.blockchain.base import BlockchainProvider
from app.utils.datetime import utcnow


class DemoProvider(BlockchainProvider):
    name: str = "Demo Provider (Local)"
    is_demo: bool = True

    def __init__(self, chain: str = "bitcoin"):
        self.blockchain = chain.lower()
        self.asset = "BTC" if self.blockchain == "bitcoin" else ("ETH" if self.blockchain == "ethereum" else "BNB")

    async def get_balance(self, address: str) -> dict[str, Any]:
        # Hash address to derive a deterministic balance
        h = int(hashlib.sha256(address.encode()).hexdigest()[:8], 16)
        balance = round((h % 5000) / 100.0, 4)
        return {
            "balance": balance,
            "pending_balance": 0.0,
            "asset": self.asset,
            "provider": self.name,
            "is_demo": True,
        }

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        now = utcnow()
        txs = []
        base_h = int(hashlib.sha256(address.encode()).hexdigest()[:8], 16)
        count = min(limit, (base_h % 15) + 5)

        known_counterparties = [
            "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
            "0x077d37a6553a309b888824e0373809071c356f9a",
        ]

        for i in range(count):
            tx_h = hashlib.sha256(f"{address}:{i}".encode()).hexdigest()
            cp = known_counterparties[i % len(known_counterparties)]
            is_incoming = i % 2 == 0
            from_addr = cp if is_incoming else address
            to_addr = address if is_incoming else cp

            txs.append(
                {
                    "tx_hash": tx_h if not self.blockchain.startswith("0x") else f"0x{tx_h}",
                    "blockchain": self.blockchain,
                    "from_address": from_addr,
                    "to_address": to_addr,
                    "amount": round(((base_h + i * 17) % 500) / 10.0 + 0.1, 4),
                    "asset": self.asset,
                    "timestamp": now - timedelta(hours=i * 6 + 1),
                    "block_number": 800000 + (count - i) * 10,
                    "confirmations": (i + 1) * 6,
                    "status": "confirmed",
                    "fee": round(0.0001 * (i + 1), 6),
                    "is_demo": True,
                }
            )
        return txs

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        return {
            "tx_hash": tx_hash,
            "blockchain": self.blockchain,
            "from_address": "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
            "to_address": "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
            "amount": 1.5,
            "asset": self.asset,
            "timestamp": utcnow() - timedelta(hours=2),
            "block_number": 834500,
            "confirmations": 12,
            "status": "confirmed",
            "fee": 0.0001,
            "is_demo": True,
        }

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        return {
            "block_number": block_number,
            "hash": hashlib.sha256(str(block_number).encode()).hexdigest(),
            "timestamp": utcnow() - timedelta(days=1),
            "tx_count": 2400,
            "is_demo": True,
        }

    async def get_address_activity(self, address: str) -> dict[str, Any]:
        now = utcnow()
        return {
            "first_seen": now - timedelta(days=90),
            "last_seen": now - timedelta(hours=2),
            "tx_count": 12,
            "is_demo": True,
        }
