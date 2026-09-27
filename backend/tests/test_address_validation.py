"""Address validation unit tests."""
from __future__ import annotations

import pytest

from app.utils.address_validation import detect_blockchain, validate_address


VALID_P2PKH = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
VALID_P2SH = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
INVALID_CHECKSUM = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNb"
VALID_BECH32 = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
INVALID_BECH32 = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5"
VALID_EVM_LOWER = "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"  # valid all-lower
VALID_EVM_CHECKSUM = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
INVALID_EVM_CHECKSUM = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAeE"
DEMO_ADDR = "DEMO-RANSOM-0001"


def test_valid_p2pkh():
    result = validate_address(VALID_P2PKH)
    assert result["valid"] is True
    assert result["blockchain"] == "bitcoin"
    assert "P2PKH" in result["reason"]


def test_valid_p2sh():
    result = validate_address(VALID_P2SH)
    assert result["valid"] is True
    assert result["blockchain"] == "bitcoin"


def test_invalid_base58_checksum():
    result = validate_address(INVALID_CHECKSUM)
    assert result["valid"] is False
    assert "checksum" in result["reason"].lower()


def test_valid_bech32():
    result = validate_address(VALID_BECH32)
    assert result["valid"] is True
    assert result["blockchain"] == "bitcoin"


def test_invalid_bech32_checksum():
    result = validate_address(INVALID_BECH32)
    assert result["valid"] is False


def test_valid_evm_addresses():
    lower = validate_address(VALID_EVM_LOWER)
    checksum = validate_address(VALID_EVM_CHECKSUM)
    assert lower["valid"] is True and lower["possible_chains"] == ["ethereum", "bsc"]
    assert checksum["valid"] is True


def test_invalid_evm_checksum():
    result = validate_address(INVALID_EVM_CHECKSUM)
    assert result["valid"] is False
    assert "EIP-55" in result["reason"]


def test_demo_address_rejected():
    """Live-only mode: simulated DEMO- addresses are rejected with an explanation."""
    result = validate_address(DEMO_ADDR)
    assert result["valid"] is False
    assert "real blockchain" in result["reason"]


def test_garbage_address():
    result = validate_address("not-an-address")
    assert result["valid"] is False
    assert result["possible_chains"] == []


def test_detect_respects_requested_chain():
    evm = "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    assert detect_blockchain(evm, "bsc")["blockchain"] == "bsc"
    assert detect_blockchain(evm, "bitcoin")["valid"] is False
    assert detect_blockchain(VALID_P2PKH, "auto")["blockchain"] == "bitcoin"


@pytest.mark.parametrize("address", ["", " ", None])
def test_empty_addresses(address):
    result = validate_address(address or "")
    assert result["valid"] is False
