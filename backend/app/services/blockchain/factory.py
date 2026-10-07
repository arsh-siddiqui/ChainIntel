"""Provider factory: maps chains/addresses to provider implementations.

ChainIntel is LIVE-only: every investigation goes through real blockchain APIs.

Selection order (first configured provider wins; failures fall through):
  ethereum / bsc : Etherscan v2 -> Moralis -> Ankr
  bitcoin        : mempool.space -> blockchain.info (optional api_code)
"""
from __future__ import annotations

from app.core.config import settings
from app.core.envelope import AppError
from app.services.blockchain.base import BlockchainProvider, ProviderError
from app.utils.address_validation import detect_blockchain

_PROVIDERS: dict[str, type[BlockchainProvider]] = {}


def _load_classes() -> None:
    if _PROVIDERS:
        return
    from app.services.blockchain.ankr import AnkrBSCProvider, AnkrEthereumProvider
    from app.services.blockchain.bitcoin import BitcoinProvider
    from app.services.blockchain.blockchain_info import BlockchainInfoProvider
    from app.services.blockchain.bsc import BSCProvider
    from app.services.blockchain.ethereum import EvmProvider
    from app.services.blockchain.moralis import MoralisBSCProvider, MoralisEthereumProvider
    from app.services.blockchain.polygon import PolygonProvider
    from app.services.blockchain.solana import SolanaProvider

    _PROVIDERS.update(
        {
            "bitcoin": BitcoinProvider,
            "blockchain-info": BlockchainInfoProvider,
            "ethereum": EvmProvider,
            "ethereum-moralis": MoralisEthereumProvider,
            "ethereum-ankr": AnkrEthereumProvider,
            "bsc": BSCProvider,
            "bsc-moralis": MoralisBSCProvider,
            "bsc-ankr": AnkrBSCProvider,
            "polygon": PolygonProvider,
            "solana": SolanaProvider,
        }
    )


def _configured_chain_providers(chain: str) -> list[str]:
    """Provider registry keys for a chain, ordered by preference, filtered to configured ones."""
    if chain == "ethereum":
        ordered = ["ethereum", "ethereum-moralis", "ethereum-ankr"]
        configured = [bool(settings.etherscan_api_key), bool(settings.moralis_api_key), bool(settings.ankr_api_key)]
    elif chain == "bsc":
        ordered = ["bsc", "bsc-moralis", "bsc-ankr"]
        configured = [
            bool(settings.bscscan_api_key or settings.etherscan_api_key),
            bool(settings.moralis_api_key),
            bool(settings.ankr_api_key),
        ]
    elif chain == "polygon":
        ordered = ["polygon"]
        configured = [True]  # standard EVM fallback/public
    elif chain == "solana":
        ordered = ["solana"]
        configured = [True]  # keyless mainnet-beta RPC
    elif chain == "bitcoin":
        ordered = ["bitcoin", "blockchain-info"]
        configured = [True, True]  # both public; preference order handles failover
    else:
        return []
    return [key for key, ok_flag in zip(ordered, configured) if ok_flag]


def get_provider(blockchain: str) -> BlockchainProvider:
    """Instantiate provider for a chain. In DEMO mode, returns DemoProvider."""
    chain = (blockchain or "").lower()
    if settings.app_mode.upper() == "DEMO":
        from app.services.blockchain.demo import DemoProvider
        return DemoProvider(chain)

    _load_classes()
    candidates = _configured_chain_providers(chain)
    if not candidates:
        if _PROVIDERS.get(chain):
            raise ProviderError("REQUIRES_CONFIGURATION", _configuration_message(chain))
        raise ProviderError("UNKNOWN_BLOCKCHAIN", f"Unsupported blockchain '{blockchain}'.")
    instances = [_PROVIDERS[key]() for key in candidates]
    if len(instances) == 1:
        return instances[0]
    from app.services.blockchain.failover import FailoverProvider

    return FailoverProvider(instances)


def _configuration_message(chain: str) -> str:
    if chain == "ethereum":
        return (
            "Ethereum provider is not configured: set ETHERSCAN_API_KEY, MORALIS_API_KEY "
            "or ANKR_API_KEY in the backend environment."
        )
    if chain == "bsc":
        return (
            "BSC provider is not configured: set BSCSCAN_API_KEY, ETHERSCAN_API_KEY, "
            "MORALIS_API_KEY or ANKR_API_KEY in the backend environment."
        )
    return f"{chain.upper()} provider is not configured."


def provider_for_address(address: str, requested: str = "auto") -> tuple[BlockchainProvider, dict]:
    """Validate + detect chain, then instantiate the matching provider."""
    detection = detect_blockchain(address, requested)
    if not detection["valid"]:
        raise AppError(400, "INVALID_WALLET", detection["reason"], {"detection": detection})
    try:
        return get_provider(detection["blockchain"]), detection
    except ProviderError as exc:
        if settings.app_mode.upper() == "DEMO":
            from app.services.blockchain.demo import DemoProvider
            return DemoProvider(detection["blockchain"]), detection
        if exc.code == "REQUIRES_CONFIGURATION":
            raise AppError(
                503,
                "REQUIRES_CONFIGURATION",
                exc.message,
                {"blockchain": detection["blockchain"], "provider_status": "NOT_CONFIGURED"},
            ) from exc
        raise AppError(503, "PROVIDER_UNAVAILABLE", exc.message, {"blockchain": detection["blockchain"], "provider_status": "UNAVAILABLE"}) from exc


def provider_status_summary() -> list[dict]:
    """Status of every provider. Never exposes API key values."""
    _load_classes()
    eth_primary = bool(settings.etherscan_api_key)
    bsc_primary = bool(settings.bscscan_api_key or settings.etherscan_api_key)
    moralis = bool(settings.moralis_api_key)
    ankr = bool(settings.ankr_api_key)
    return [
        {"name": "mempool.space (Bitcoin)", "blockchain": "bitcoin", "status": "CONFIGURED", "key_configured": None, "is_demo": False},
        {"name": "blockchain.info (Bitcoin fallback)", "blockchain": "bitcoin", "status": "CONFIGURED", "key_configured": bool(settings.blockchain_api_key) or None, "is_demo": False},
        {"name": "Etherscan v2 (Ethereum)", "blockchain": "ethereum", "status": "CONFIGURED" if eth_primary else "NOT_CONFIGURED", "key_configured": eth_primary, "is_demo": False},
        {"name": "Etherscan v2 (BNB Smart Chain)", "blockchain": "bsc", "status": "CONFIGURED" if bsc_primary else "NOT_CONFIGURED", "key_configured": bsc_primary, "is_demo": False},
        {"name": "Moralis (Ethereum)", "blockchain": "ethereum", "status": "CONFIGURED" if moralis else "NOT_CONFIGURED", "key_configured": moralis, "is_demo": False},
        {"name": "Moralis (BNB Smart Chain)", "blockchain": "bsc", "status": "CONFIGURED" if moralis else "NOT_CONFIGURED", "key_configured": moralis, "is_demo": False},
        {"name": "Ankr (Ethereum)", "blockchain": "ethereum", "status": "CONFIGURED" if ankr else "NOT_CONFIGURED", "key_configured": ankr, "is_demo": False},
        {"name": "Ankr (BNB Smart Chain)", "blockchain": "bsc", "status": "CONFIGURED" if ankr else "NOT_CONFIGURED", "key_configured": ankr, "is_demo": False},
    ]
