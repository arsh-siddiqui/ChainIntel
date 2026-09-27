"""BNB Smart Chain provider (Etherscan v2 multichain, chain id 56)."""
from __future__ import annotations

from app.core.config import settings
from app.services.blockchain.base import ProviderError
from app.services.blockchain.ethereum import EvmProvider


class BSCProvider(EvmProvider):
    name = "etherscan-v2 (bsc)"
    blockchain = "bsc"
    asset = "BNB"
    chain_id = 56

    def __init__(self, api_key: str | None = None):
        key = api_key or settings.bscscan_api_key or settings.etherscan_api_key
        if not key:
            raise ProviderError(
                "REQUIRES_CONFIGURATION",
                "BSC provider is not configured: set BSCSCAN_API_KEY (or ETHERSCAN_API_KEY) in the backend environment.",
            )
        super().__init__(api_key=key)
