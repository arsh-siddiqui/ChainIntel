"""Tests for the multi-provider layer: Moralis, Ankr, blockchain.info, failover factory."""
from __future__ import annotations

import pytest

from app.core.config import settings
from app.services.blockchain.ankr import AnkrEthereumProvider
from app.services.blockchain.base import ProviderError
from app.services.blockchain.bitcoin import BitcoinProvider
from app.services.blockchain.blockchain_info import BlockchainInfoProvider
from app.services.blockchain.ethereum import EvmProvider
from app.services.blockchain.failover import FailoverProvider
from app.services.blockchain.factory import get_provider
from app.services.blockchain.moralis import MoralisEthereumProvider


class StubProvider:
    """Minimal provider stub for failover mechanics (no HTTP)."""

    def __init__(self, name: str, behavior):
        self.name = name
        self._behavior = behavior  # callable(method_name, *args) -> result | raises

    async def get_balance(self, address):
        return self._behavior("get_balance", address)

    async def get_transactions(self, address, limit=100):
        return self._behavior("get_transactions", address, limit)

    async def get_transaction(self, tx_hash):
        return self._behavior("get_transaction", tx_hash)

    async def get_block_info(self, block_number):
        return self._behavior("get_block_info", block_number)

    async def get_address_activity(self, address):
        return self._behavior("get_address_activity", address)


# --------------------------------------------------------------------------
# FailoverProvider mechanics
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_failover_retries_next_provider_on_unavailable():
    def fail(method, *args):
        raise ProviderError("PROVIDER_UNAVAILABLE", "down")

    ok = StubProvider("secondary", lambda method, *a: {"balance": 1.0})
    wrapper = FailoverProvider([StubProvider("primary", fail), ok])
    assert await wrapper.get_balance("x") == {"balance": 1.0}
    assert wrapper.name == "primary"  # identity follows the primary


@pytest.mark.anyio
async def test_failover_raises_last_error_when_all_fail():
    def fail(method, *args):
        raise ProviderError("PROVIDER_UNAVAILABLE", "down")

    wrapper = FailoverProvider([StubProvider("a", fail), StubProvider("b", fail)])
    with pytest.raises(ProviderError) as excinfo:
        await wrapper.get_balance("x")
    assert excinfo.value.code == "PROVIDER_UNAVAILABLE"


@pytest.mark.anyio
async def test_failover_does_not_retry_not_found():
    def not_found(method, *args):
        raise ProviderError("NOT_FOUND", "missing")

    def ok(method, *args):
        return {"tx": True}

    wrapper = FailoverProvider([StubProvider("a", not_found), StubProvider("b", ok)])
    with pytest.raises(ProviderError) as excinfo:
        await wrapper.get_transaction("0xabc")
    assert excinfo.value.code == "NOT_FOUND"  # propagates, no fallback


# --------------------------------------------------------------------------
# Factory selection
# --------------------------------------------------------------------------

def _clear_evm_keys(monkeypatch):
    for attr in ("etherscan_api_key", "moralis_api_key", "ankr_api_key", "bscscan_api_key"):
        monkeypatch.setattr(settings, attr, "")


def test_ethereum_without_any_key_requires_configuration(monkeypatch):
    _clear_evm_keys(monkeypatch)
    with pytest.raises(ProviderError) as excinfo:
        get_provider("ethereum")
    assert excinfo.value.code == "REQUIRES_CONFIGURATION"
    assert "ETHERSCAN_API_KEY" in excinfo.value.message
    assert "MORALIS_API_KEY" in excinfo.value.message
    assert "ANKR_API_KEY" in excinfo.value.message


def test_etherscan_key_selects_primary(monkeypatch):
    _clear_evm_keys(monkeypatch)
    monkeypatch.setattr(settings, "etherscan_api_key", "k")
    provider = get_provider("ethereum")
    assert provider.name == "etherscan-v2"
    assert not isinstance(provider, FailoverProvider)


def test_moralis_only_returns_moralis_directly(monkeypatch):
    _clear_evm_keys(monkeypatch)
    monkeypatch.setattr(settings, "moralis_api_key", "k")
    provider = get_provider("ethereum")
    # A single configured provider is returned as-is; no failover wrapper needed.
    assert provider.name == "moralis (ethereum)"
    assert not isinstance(provider, FailoverProvider)


def test_all_three_keys_build_full_failover_chain(monkeypatch):
    _clear_evm_keys(monkeypatch)
    monkeypatch.setattr(settings, "etherscan_api_key", "k1")
    monkeypatch.setattr(settings, "moralis_api_key", "k2")
    monkeypatch.setattr(settings, "ankr_api_key", "k3")
    provider = get_provider("bsc")
    assert isinstance(provider, FailoverProvider)
    assert [p.name for p in provider.providers] == ["etherscan-v2 (bsc)", "moralis (bsc)", "ankr (bsc)"]


def test_bitcoin_always_configured_with_two_candidates(monkeypatch):
    provider = get_provider("bitcoin")
    assert isinstance(provider, FailoverProvider)
    assert [p.name for p in provider.providers] == ["mempool.space", "blockchain.info"]


# --------------------------------------------------------------------------
# Moralis normalization
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_moralis_balance_and_transactions(monkeypatch):
    provider = MoralisEthereumProvider(api_key="test")

    async def fake_get(path, params=None):
        if path.endswith("/balance"):
            return {"balance": "1000000000000000000"}
        if path == "/0xabc":
            return {
                "result": [
                    {
                        "hash": "0xtx1",
                        "from_address": "0xABC",
                        "to_address": "0xdef",
                        "value": "2000000000000000000",
                        "block_number": 100,
                        "block_timestamp": "2024-05-01T10:00:00.000Z",
                        "gas_used": "21000",
                        "gas_price": "1000000000",
                        "confirmations": 5,
                    }
                ],
                "cursor": None,
            }
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(provider, "_get", fake_get)
    balance = await provider.get_balance("0xabc")
    assert balance == {"balance": 1.0, "asset": "ETH", "provider": "moralis (ethereum)", "is_demo": False}

    txs = await provider.get_transactions("0xabc")
    assert len(txs) == 1
    tx = txs[0]
    assert tx["tx_hash"] == "0xtx1"
    assert tx["amount"] == 2.0
    assert tx["asset"] == "ETH"
    assert tx["blockchain"] == "ethereum"
    assert tx["direction"] == "outgoing"
    assert tx["status"] == "confirmed"
    assert tx["fee"] == round(21000 * 1000000000 / 1e18, 8)
    assert tx["timestamp"] is not None and tx["timestamp"].year == 2024


# --------------------------------------------------------------------------
# Ankr normalization
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ankr_balance_and_transactions(monkeypatch):
    """Pins the REAL Ankr shapes observed live (2026-09):
    balance assets use tokenType/tokenDecimals/balanceRawInteger (decimal string);
    transactions arrive in ETH JSON-RPC style with hex quantities and from/to."""
    provider = AnkrEthereumProvider(api_key="test")

    async def fake_advanced(method, params):
        if method == "ankr_getAccountBalance":
            return {
                "result": {
                    "assets": [
                        {
                            "blockchain": "eth",
                            "tokenType": "NATIVE",
                            "contractAddress": None,
                            "tokenSymbol": "ETH",
                            "tokenDecimals": 18,
                            "balance": "1.5",
                            "balanceRawInteger": "1500000000000000000",
                        }
                    ]
                }
            }
        if method == "ankr_getTransactionsByAddress":
            return {
                "result": {
                    "transactions": [
                        {
                            "hash": "0xtx9",
                            "from": "0x111",
                            "to": "0xABC",
                            "value": "0x29A2241AF62C0000",  # 3 ETH in hex wei
                            "blockNumber": "0xC8",          # 200
                            "blockTimestamp": "2024-06-01T12:30:00Z",
                            "gasUsed": "0x5246",
                            "gasPrice": "0x3B9ACA00",       # 1 gwei
                            "status": "0x1",
                        }
                    ]
                }
            }
        raise AssertionError(f"unexpected method {method}")

    monkeypatch.setattr(provider, "_advanced", fake_advanced)
    balance = await provider.get_balance("0xabc")
    assert balance["balance"] == 1.5

    txs = await provider.get_transactions("0xabc")
    tx = txs[0]
    assert tx["tx_hash"] == "0xtx9"
    assert tx["amount"] == 3.0
    assert tx["direction"] == "incoming"
    assert tx["status"] == "confirmed"
    assert tx["block_number"] == 200
    assert tx["fee"] == round(0x5246 * 0x3B9ACA00 / 1e18, 8)
    assert tx["timestamp"] is not None and tx["timestamp"].month == 6


# --------------------------------------------------------------------------
# blockchain.info (Bitcoin fallback)
# --------------------------------------------------------------------------

def test_blockchain_info_normalize_directions():
    raw = {
        "hash": "h1",
        "time": 1714521600,
        "block_height": 800000,
        "fee": 1000,
        "inputs": [{"prev_out": {"addr": "A", "value": 300000}}],
        "out": [
            {"addr": "A", "value": 50000},   # change back to sender
            {"addr": "B", "value": 250000},  # actual recipient
        ],
    }
    # Outgoing from A: net sent to B.
    out_tx = BlockchainInfoProvider._normalize(raw, address="A")
    assert out_tx["direction"] == "outgoing"
    assert out_tx["to_address"] == "B"
    assert out_tx["amount"] == 0.0025
    # Incoming for B.
    in_tx = BlockchainInfoProvider._normalize(raw, address="B")
    assert in_tx["direction"] == "incoming"
    assert in_tx["from_address"] == "A"
    assert in_tx["amount"] == 0.0025
    # No address context (single-tx lookup): unknown direction, raw endpoints.
    raw_tx = BlockchainInfoProvider._normalize(raw, address=None)
    assert raw_tx["direction"] == "unknown"
    assert raw_tx["from_address"] == "A"
    assert raw_tx["to_address"] == "B"


@pytest.mark.anyio
async def test_blockchain_info_sends_api_code_when_configured(monkeypatch):
    provider = BlockchainInfoProvider(api_key="mycode")
    captured = {}

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"final_balance": 150000, "n_tx": 1, "txs": []}

    async def fake_get(path, params=None):
        captured["path"] = path
        captured["params"] = params
        return FakeResponse().json()

    async def real_get(path, params=None):
        return await provider._get(path, params)

    # Intercept at the HTTP boundary instead: patch httpx client usage.
    class FakeClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            return False
        async def get(self, url, params=None):
            captured["url"] = url
            captured["params"] = params
            return FakeResponse()

    import httpx as _httpx

    def fake_async_client(*args, **kwargs):
        return FakeClient()

    monkeypatch.setattr(_httpx, "AsyncClient", fake_async_client)
    balance = await provider.get_balance("addr")
    assert balance["balance"] == 0.0015
    assert captured["params"]["api_code"] == "mycode"
    assert captured["params"]["cors"] == "true"


# --------------------------------------------------------------------------
# mempool.space single-tx lookup (no address context)
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_mempool_get_transaction_has_no_address_context(monkeypatch):
    provider = BitcoinProvider()

    raw_tx = {
        "txid": "tx1",
        "fee": 500,
        "status": {"confirmed": True, "block_height": 800000, "block_time": 1714521600},
        "vin": [{"prevout": {"scriptpubkey_address": "A", "value": 300000}}],
        "vout": [
            {"scriptpubkey_address": "A", "value": 50000},
            {"scriptpubkey_address": "B", "value": 250000},
        ],
    }

    async def fake_get(path):
        if path == "/tx/tx1":
            return raw_tx
        if path == "/blocks/tip/height":
            return 800010
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(provider, "_get", fake_get)
    tx = await provider.get_transaction("tx1")
    assert tx["direction"] == "unknown"
    assert tx["from_address"] == "A"
    assert tx["to_address"] == "B"
    assert tx["confirmations"] == 11
