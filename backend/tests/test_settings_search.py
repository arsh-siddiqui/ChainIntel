"""Settings, search and audit tests."""
from __future__ import annotations

from app.core.config import settings


def _set_evm_keys(monkeypatch, **keys):
    for attr in ("etherscan_api_key", "moralis_api_key", "ankr_api_key", "bscscan_api_key"):
        monkeypatch.setattr(settings, attr, keys.get(attr, ""))


def test_providers_never_leak_keys(client, monkeypatch):
    """Status flips with configuration and raw key values never appear.

    Keys are set explicitly so the test is hermetic regardless of backend/.env.
    """
    _set_evm_keys(monkeypatch)  # nothing configured
    response = client.get("/api/settings/providers")
    data = response.json()["data"]
    assert data["mode"] == "LIVE"
    providers = data["blockchain_providers"]
    assert {p["blockchain"] for p in providers} == {"bitcoin", "ethereum", "bsc"}
    etherscan = next(p for p in providers if p["name"].startswith("Etherscan"))
    assert etherscan["status"] == "NOT_CONFIGURED"
    assert all(p["blockchain"] != "demo" for p in providers)

    _set_evm_keys(monkeypatch, etherscan_api_key="secret-etherscan-value")
    response = client.get("/api/settings/providers")
    providers = response.json()["data"]["blockchain_providers"]
    etherscan = next(p for p in providers if p["name"].startswith("Etherscan"))
    assert etherscan["status"] == "CONFIGURED"
    assert etherscan["key_configured"] is True
    assert "secret-etherscan-value" not in response.text  # the value itself never leaks


def test_mode_endpoint_removed(client):
    """The runtime DEMO/LIVE switch is gone: the app is always LIVE."""
    response = client.post("/api/settings/mode", json={"mode": "LIVE"})
    assert response.status_code == 404


def test_overview_redacts_database_url(client):
    data = client.get("/api/settings/overview").json()["data"]
    assert "<redacted>" in data["database"]["url"]


def test_global_search_categories(client, monkeypatch):
    from tests.fake_provider import BTC_ADDRESS, install_fake_provider

    install_fake_provider(monkeypatch, "bitcoin")
    client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS})
    client.post("/api/cases", json={"title": "Searchable Case Alpha"})

    response = client.get(f"/api/search?q={BTC_ADDRESS}")
    data = response.json()["data"]
    assert data["wallets"]

    response = client.get("/api/search?q=fake-tx")
    assert response.json()["data"]["transactions"]

    response = client.get("/api/search?q=Searchable Case Alpha")
    assert response.json()["data"]["cases"]


def test_audit_log_records_actions(client, monkeypatch):
    from tests.fake_provider import BTC_ADDRESS, install_fake_provider

    install_fake_provider(monkeypatch, "bitcoin")
    client.post("/api/cases", json={"title": "Audit Test Case"})
    client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS})
    response = client.get("/api/audit-log?page_size=50")
    actions = {item["action"] for item in response.json()["data"]}
    assert "case_created" in actions
    assert "wallet_investigated" in actions
