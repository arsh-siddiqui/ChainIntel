"""Transaction explorer tests (hermetic, FakeProvider-backed)."""
from __future__ import annotations

from tests.fake_provider import BTC_ADDRESS, TXS, install_fake_provider


def _seed(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")
    client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS})


def test_list_transactions(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.get("/api/transactions?page=1&page_size=10")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] >= 3
    tx = body["data"][0]
    assert {"tx_hash", "from_address", "to_address", "amount", "asset", "timestamp"} <= set(tx)


def test_transaction_search_and_filter(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.get("/api/transactions?search=fake-tx-out-1")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["tx_hash"] == "fake-tx-out-1"

    response = client.get("/api/transactions?min_amount=1&sort_by=amount&sort_dir=desc")
    amounts = [t["amount"] for t in response.json()["data"]]
    assert amounts == sorted(amounts, reverse=True)
    assert all(a >= 1 for a in amounts)


def test_transaction_detail_and_404(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.get("/api/transactions/fake-tx-out-1")
    assert response.status_code == 200
    tx = response.json()["data"]
    assert tx["tx_hash"] == "fake-tx-out-1"
    assert tx["explorer_url"].startswith("https://")  # live chains always have an explorer

    response = client.get("/api/transactions/fake-tx-99999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TRANSACTION_NOT_FOUND"


def test_wallet_transactions_direction_filter(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.get(f"/api/wallets/{BTC_ADDRESS}/transactions?direction=incoming")
    data = response.json()["data"]
    assert data
    assert all(t["direction"] == "incoming" and t["to_address"] == BTC_ADDRESS for t in data)


def test_wallet_transactions_amount_range(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.get(f"/api/wallets/{BTC_ADDRESS}/transactions?min_amount=0.5&max_amount=1.3&page_size=100")
    data = response.json()["data"]
    assert data
    assert all(0.5 <= t["amount"] <= 1.3 for t in data)
