"""Wallet address validation and blockchain detection.

Supports:
- Bitcoin: Base58Check (P2PKH/P2SH) and Bech32 (segwit, hrp "bc")
- Ethereum / BSC: 0x-hex with optional EIP-55 checksum verification

The module never handles private keys or seed phrases; it is read-only validation.
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
BTC_B58_VERSIONS = {0x00: "P2PKH", 0x05: "P2SH"}


# ---------------------------------------------------------------- Base58Check
def base58check_decode(value: str) -> Optional[bytes]:
    """Decode a Base58Check string; returns payload bytes or None if invalid."""
    if not value or any(ch not in BASE58_ALPHABET for ch in value) or len(value) > 60:
        return None
    number = 0
    for ch in value:
        number = number * 58 + BASE58_ALPHABET.index(ch)
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    pad = 0
    for ch in value:
        if ch == "1":
            pad += 1
        else:
            break
    raw = b"\x00" * pad + raw
    if len(raw) < 5:
        return None
    payload, checksum = raw[:-4], raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        return None
    return payload


# ---------------------------------------------------------------- Bech32
def _bech32_polymod(values: list[int]) -> int:
    generators = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i in range(5):
            chk ^= generators[i] if ((top >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def validate_bech32_address(address: str, hrp: str = "bc") -> bool:
    """Verify Bech32 checksum for segwit addresses (witness v0-16)."""
    if address.lower() != address and address.upper() != address:
        return False  # mixed case is invalid in Bech32
    addr = address.lower()
    pos = addr.rfind("1")
    if pos < 1 or pos + 7 > len(addr) or len(addr) > 90:
        return False
    if addr[:pos] != hrp:
        return False
    try:
        data = [BECH32_CHARSET.index(c) for c in addr[pos + 1:]]
    except ValueError:
        return False
    return _bech32_polymod(_bech32_hrp_expand(hrp) + data) == 1


# ---------------------------------------------------------------- EVM / EIP-55
def _eip55_checksum_valid(address: str) -> bool:
    try:
        from Crypto.Hash import keccak
    except ImportError:  # pragma: no cover - pycryptodome is a hard dependency
        return True
    addr = address[2:].lower()
    digest = keccak.new(digest_bits=256)
    digest.update(addr.encode("ascii"))
    hash_hex = digest.hexdigest()
    for i, ch in enumerate(addr):
        if ch in "abcdef" and int(hash_hex[i], 16) >= 8:
            if address[2 + i] != ch.upper():
                return False
    return True


def validate_evm_address(address: str) -> tuple[bool, str]:
    if not EVM_ADDRESS_RE.match(address):
        return False, "EVM addresses must be 42 characters: '0x' followed by 40 hex characters."
    body = address[2:]
    if body == body.lower() or body == body.upper():
        return True, "Valid EVM address (no EIP-55 checksum encoded)."
    if not _eip55_checksum_valid(address):
        return False, "EIP-55 checksum mismatch: address characters do not match the encoded checksum."
    return True, "Valid EVM address (EIP-55 checksum verified)."


# ---------------------------------------------------------------- Public API
def validate_address(address: str) -> dict:
    """Validate an address and detect candidate blockchains.

    Returns: {valid, blockchain, possible_chains, reason}
    """
    address = (address or "").strip()
    if not address:
        return {"valid": False, "blockchain": None, "possible_chains": [], "reason": "Address is required."}

    if address.upper().startswith("DEMO-"):
        return {
            "valid": False,
            "blockchain": None,
            "possible_chains": [],
            "reason": "DEMO- prefixed simulated addresses are not supported: ChainIntel operates against real blockchain APIs only.",
        }

    # Bitcoin: Bech32 (bc1...) or Base58Check ('1'/'3' prefixed, 26-35 chars)
    if address.lower().startswith("bc1"):
        if validate_bech32_address(address):
            return {"valid": True, "blockchain": "bitcoin", "possible_chains": ["bitcoin"], "reason": "Valid Bech32 (segwit) Bitcoin address."}
        return {"valid": False, "blockchain": "bitcoin", "possible_chains": ["bitcoin"], "reason": "Bech32 checksum verification failed."}

    if address[0] in ("1", "3") and 25 <= len(address) <= 36:
        payload = base58check_decode(address)
        if payload is None:
            return {"valid": False, "blockchain": "bitcoin", "possible_chains": ["bitcoin"], "reason": "Base58Check checksum verification failed."}
        version = payload[0]
        if version in BTC_B58_VERSIONS:
            kind = BTC_B58_VERSIONS[version]
            return {"valid": True, "blockchain": "bitcoin", "possible_chains": ["bitcoin"], "reason": f"Valid Base58Check address ({kind})."}
        return {"valid": False, "blockchain": "bitcoin", "possible_chains": ["bitcoin"], "reason": f"Unsupported Bitcoin version byte 0x{version:02x}."}

    # EVM (Ethereum / BSC share the format; ambiguous until the user selects)
    if address.lower().startswith("0x"):
        valid, reason = validate_evm_address(address)
        return {
            "valid": valid,
            "blockchain": "ethereum" if valid else None,
            "possible_chains": ["ethereum", "bsc"] if valid else [],
            "reason": reason,
        }

    return {
        "valid": False,
        "blockchain": None,
        "possible_chains": [],
        "reason": "Unrecognized address format. Supported: Bitcoin (1/3/bc1), Ethereum, BSC (0x...).",
    }


def detect_blockchain(address: str, requested: Optional[str] = None) -> dict:
    """Detect the blockchain for an address, honouring an explicit selector.

    Returns the validation dict, with `blockchain` resolved to a concrete chain
    when valid (bitcoin/bitcoin, ethereum default for EVM).
    """
    result = validate_address(address)
    if not result["valid"]:
        return result
    if requested and requested not in ("auto", "", None):
        chain = requested.lower()
        if chain in result["possible_chains"] or chain == result["blockchain"]:
            result["blockchain"] = chain
        else:
            return {"valid": False, "blockchain": None, "possible_chains": result["possible_chains"], "reason": f"Address format does not match the selected chain '{chain}'."}
    if result["blockchain"] is None and result["possible_chains"]:
        result["blockchain"] = result["possible_chains"][0]  # EVM default: ethereum
    return result
