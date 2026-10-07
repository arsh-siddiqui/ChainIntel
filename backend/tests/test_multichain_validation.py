"""Comprehensive unit tests for multichain wallet address validation."""
from __future__ import annotations

import pytest
from app.utils.address_validation import detect_blockchain


@pytest.mark.parametrize(
    "address,expected_chain",
    [
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin"),  # Legacy Base58 P2PKH
        ("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", "bitcoin"),  # Base58 P2SH
        ("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "bitcoin"),  # SegWit Bech32 P2WPKH
        ("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum"),  # EVM Tornado Cash
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ethereum"),  # EVM vitalik.eth
        ("0x0000000000000000000000000000000000000000", "ethereum"),  # EVM Null Address
        ("5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", "solana"),  # Solana Base58
    ],
)
def test_detect_blockchain_valid(address, expected_chain):
    res = detect_blockchain(address)
    assert res["valid"] is True
    assert res["blockchain"] == expected_chain


@pytest.mark.parametrize(
    "address",
    [
        "",
        "   ",
        "invalid_address_string",
        "0x123",  # Too short for EVM
        "0x12d6621e19a95080e0276664261065623b1a0623GGGG",  # Invalid hex char
        "NOT-A-VALID-BASE58-SOLANA-WALLET!!!",
    ],
)
def test_detect_blockchain_invalid(address):
    res = detect_blockchain(address)
    assert res["valid"] is False


def test_validate_address_explicit_chain():
    # Explicit chain matching via detect_blockchain
    assert detect_blockchain("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin")["valid"] is True
    assert detect_blockchain("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum")["valid"] is True
    assert detect_blockchain("0x12d6621e19a95080e0276664261065623b1a0623", "bsc")["valid"] is True
    assert detect_blockchain("0x12d6621e19a95080e0276664261065623b1a0623", "polygon")["valid"] is True

    # Mismatched chain rejection
    assert detect_blockchain("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "ethereum")["valid"] is False
    assert detect_blockchain("0x12d6621e19a95080e0276664261065623b1a0623", "bitcoin")["valid"] is False
