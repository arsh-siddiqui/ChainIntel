"""Unit and integration tests for OSINT correlation and sources."""
from __future__ import annotations

import pytest
from app.services.osint import correlate_wallet, external_sources_status


def test_osint_bitcoin_routing():
    """Verify Bitcoin addresses receive Bitcoin-relevant OSINT providers."""
    btc_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    data = correlate_wallet(btc_address)

    assert data["query"] == btc_address
    assert data["provider_count"] >= 6

    source_names = [r["source_name"] for r in data["results"]]
    assert "Bitcoin Who's Who" in source_names
    assert "Chainabuse" in source_names
    assert "Blockstream Explorer" in source_names
    assert "Blockchain.com Explorer" in source_names
    assert "BitRef" in source_names
    assert "Community Forensics (X / Twitter)" in source_names

    # Etherscan should not be queried for a Bitcoin address
    assert "Etherscan Public Reports & Labels" not in source_names


def test_osint_evm_routing():
    """Verify EVM addresses receive Ethereum-relevant OSINT providers."""
    eth_address = "0x7f367cc41522ce07553e8435b8b4f7257b434f4e"
    data = correlate_wallet(eth_address)

    assert data["query"] == eth_address
    assert data["provider_count"] >= 6

    source_names = [r["source_name"] for r in data["results"]]
    assert "Arkham Intelligence" in source_names
    assert "Etherscan Public Reports & Labels" in source_names
    assert "DeBank Web3 Profile" in source_names
    assert "Chainabuse" in source_names
    assert "Blockchair Explorer" in source_names
    assert "Community Forensics (X / Twitter)" in source_names

    # Bitcoin-only sources should not be queried for an EVM address
    assert "Bitcoin Who's Who" not in source_names
    assert "BitRef" not in source_names


def test_osint_urls_valid_and_encoded():
    """Ensure all external search URLs are properly formed with the target address."""
    addr = "12ib7dApVFvg82TXKycWBNpN8kFyiAN1dr"
    data = correlate_wallet(addr)

    for item in data["results"]:
        url = item.get("external_search_url")
        assert url is not None
        assert url.startswith("https://")
        assert addr in url


def test_osint_forensic_integrity():
    """Ensure link-only providers maintain forensic integrity without faking findings."""
    data = correlate_wallet("1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF")

    # Link-only sources must never fabricate 'FOUND' status
    for item in data["results"]:
        assert item["status"] == "UNAVAILABLE"
        assert item["finding"] is None


def test_osint_api_endpoints(client):
    """Test FastAPI OSINT endpoints return expected HTTP 200 envelopes."""
    # 1. Sources status
    resp = client.get("/api/osint/sources")
    assert resp.status_code == 200
    sources_data = resp.json()["data"]["sources"]
    assert len(sources_data) >= 8

    # 2. Search address
    target = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    search_resp = client.get(f"/api/osint/search/{target}")
    assert search_resp.status_code == 200
    search_body = search_resp.json()["data"]
    assert search_body["validation"]["valid"] is True
    assert search_body["correlation"]["provider_count"] >= 6


def test_restricted_analyst_record_lifecycle(client):
    """Test adding and retrieving analyst notes via the restricted OSINT API."""
    target_wallet = "0x7f367cc41522ce07553e8435b8b4f7257b434f4e"
    payload = {
        "wallet_address": target_wallet,
        "source": "Forensic Analyst Note",
        "record_type": "ANALYST_NOTE",
        "finding": "Identified in Lazarus Group Axie Infinity exploit cluster.",
        "confidence": 0.95,
        "reference_url": "https://justice.gov/opa/pr/lazarus-crypto-seizure",
        "notes": "Verified against FBI cyber advisory.",
    }

    # Add restricted record
    post_resp = client.post("/api/osint/restricted", json=payload)
    assert post_resp.status_code == 200
    post_data = post_resp.json()["data"]
    assert post_data["wallet_address"] == target_wallet
    assert post_data["finding"] == payload["finding"]

    # Fetch restricted records for the wallet
    get_resp = client.get(f"/api/osint/restricted/{target_wallet}")
    assert get_resp.status_code == 200
    records = get_resp.json()["data"]["records"]
    assert len(records) >= 1
    assert any(r["finding"] == payload["finding"] for r in records)
