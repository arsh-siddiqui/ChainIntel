"""Failover wrapper: delegates provider calls across configured candidates.

The wrapper satisfies the BlockchainProvider interface, so services can use it
transparently. A failing candidate is skipped only on transient/configuration
errors (UNAVAILABLE / RATE_LIMITED / REQUIRES_CONFIGURATION); NOT_FOUND and
UNKNOWN_BLOCKCHAIN propagate immediately. Data is never faked on failure —
if every candidate fails, the last upstream error is re-raised.
"""
from __future__ import annotations

from typing import Any

from app.services.blockchain.base import BlockchainProvider, ProviderError

_RETRYABLE = ("PROVIDER_UNAVAILABLE", "PROVIDER_RATE_LIMITED", "REQUIRES_CONFIGURATION")


class FailoverProvider(BlockchainProvider):
    def __init__(self, providers: list[BlockchainProvider]):
        if not providers:
            raise ProviderError("PROVIDER_UNAVAILABLE", "No providers configured for failover.")
        self._providers = providers
        self._primary = providers[0]

    # -- identity delegated to the primary provider ------------------------
    @property
    def name(self) -> str:
        return self._primary.name

    @property
    def blockchain(self) -> str:  # type: ignore[override]
        return self._primary.blockchain

    @property
    def asset(self) -> str:  # type: ignore[override]
        return self._primary.asset

    @property
    def is_demo(self) -> bool:  # type: ignore[override]
        return self._primary.is_demo

    @property
    def providers(self) -> list[BlockchainProvider]:
        return list(self._providers)

    async def _attempt(self, method_name: str, *args, **kwargs) -> Any:
        last_error: ProviderError | None = None
        for provider in self._providers:
            try:
                return await getattr(provider, method_name)(*args, **kwargs)
            except ProviderError as exc:
                if exc.code not in _RETRYABLE:
                    raise
                last_error = exc
        if last_error:
            raise last_error
        raise ProviderError("PROVIDER_UNAVAILABLE", "No provider configured for failover.")

    # -- delegated interface ------------------------------------------------
    async def get_balance(self, address: str) -> dict[str, Any]:
        return await self._attempt("get_balance", address)

    async def get_transactions(self, address: str, limit: int = 100) -> list[dict[str, Any]]:
        return await self._attempt("get_transactions", address, limit)

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        return await self._attempt("get_transaction", tx_hash)

    async def get_block_info(self, block_number: int) -> dict[str, Any]:
        return await self._attempt("get_block_info", block_number)

    async def get_address_activity(self, address: str) -> dict[str, Any]:
        return await self._attempt("get_address_activity", address)
