"""Wallet investigation pipeline tests (hermetic, FakeProvider-backed)."""
from __future__ import annotations

from tests.fake_provider import BTC_ADDRESS, ETH_ADDRESS, TXS, install_fake_provider

REAL_ETH_ADDRESS = "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"


def test_investigate_btc_wallet(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")
    response = client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS, "blockchain": "auto"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    assert data["address"] == BTC_ADDRESS
    assert data["blockchain"] == "bitcoin"
    assert data["mode"] == "LIVE"
    assert data["provider"]["is_demo"] is False

    wallet = data["wallet"]
    assert wallet["transaction_count"] > 0
    assert wallet["incoming_volume"] > 0
    assert wallet["unique_counterparties"] > 0

    # Built-in entity tags / threat records match for genesis address.
    assert isinstance(data["threats"], list)

    # OSINT: link-only providers surface UNAVAILABLE, never fabricated findings.
    statuses = {r["status"] for r in data["osint"]["results"]}
    assert "UNAVAILABLE" in statuses
    assert "FOUND" not in statuses

    # Graph built with nodes/edges in the documented format.
    graph = data["graph"]
    assert graph["stats"]["node_count"] >= 3
    assert graph["nodes"] and graph["edges"]
    node = graph["nodes"][0]
    assert {"id", "label", "type", "risk"} <= set(node)
    edge = graph["edges"][0]
    assert {"source", "target", "amount", "asset", "tx_hash"} <= set(edge)

    # Transparent risk engine with disclaimer (clean data -> LOW).
    risk = data["risk"]
    assert risk["band"] in ("LOW", "ELEVATED", "MODERATE")
    assert "not a determination of unlawful activity" in risk["disclaimer"]

    assert data["investigation_id"]


def test_investigate_demo_address_rejected(client):
    response = client.post("/api/wallets/investigate", json={"address": "DEMO-RANSOM-0001"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "INVALID_WALLET"
    assert "real blockchain" in body["error"]["message"]


def test_investigate_invalid_wallet(client):
    response = client.post("/api/wallets/investigate", json={"address": "definitely-not-valid"})
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_WALLET"


def test_investigate_unconfigured_provider(client, monkeypatch):
    """EVM provider without keys -> REQUIRES_CONFIGURATION, never fake data."""
    from app.core.config import settings

    for attr in ("etherscan_api_key", "moralis_api_key", "ankr_api_key", "bscscan_api_key"):
        monkeypatch.setattr(settings, attr, "")
    response = client.post("/api/wallets/investigate", json={"address": REAL_ETH_ADDRESS})
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "REQUIRES_CONFIGURATION"
    assert body["meta"]["provider_status"] == "NOT_CONFIGURED"


def test_get_wallet_returns_cached_investigation(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")
    client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS})
    response = client.get(f"/api/wallets/{BTC_ADDRESS}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["investigation"] is not None
    assert data["bundle"] is not None
    assert data["bundle"]["address"] == BTC_ADDRESS


def test_pipeline_steps_endpoint(client):
    response = client.get("/api/wallets/pipeline-steps")
    steps = response.json()["data"]["steps"]
    assert steps[0].startswith("Validating")
    assert steps[-1] == "Completed"
