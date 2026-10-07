"""Polygon (MATIC) blockchain provider using EVM compatible endpoint."""
from __future__ import annotations

from typing import Any

from app.services.blockchain.ethereum import EvmProvider


class PolygonProvider(EvmProvider):
    """Polygon (MATIC) provider using Etherscan v2 or PolygonScan API."""

    name = "polygonscan"
    blockchain = "polygon"
    asset = "MATIC"
    chain_id = 137  # Polygon Mainnet
    is_demo = False
