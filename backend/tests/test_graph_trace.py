"""Graph and fund-flow trace tests (hermetic, FakeProvider-backed)."""
from __future__ import annotations

from tests.fake_provider import BTC_ADDRESS, CP1, CP2, install_fake_provider


def _seed(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")
    client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS})


def test_wallet_graph(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.get(f"/api/wallets/{BTC_ADDRESS}/graph?hops=3")
    assert response.status_code == 200
    graph = response.json()["data"]
    ids = {n["id"] for n in graph["nodes"]}
    assert BTC_ADDRESS in ids
    assert graph["stats"]["node_count"] == len(graph["nodes"])
    assert graph["stats"]["edge_count"] == len(graph["edges"])


def test_graph_nodes_have_no_demo_flag(client, monkeypatch):
    _seed(client, monkeypatch)
    graph = client.get(f"/api/wallets/{BTC_ADDRESS}/graph").json()["data"]
    for node in graph["nodes"]:
        assert "demo" not in node
        assert node["type"] in ("wallet", "victim", "ransomware", "scam", "mixer", "exchange")


def test_trace_outgoing_to_target(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.post(
        "/api/graph/trace",
        json={"wallet_address": BTC_ADDRESS, "direction": "outgoing", "target_address": CP1, "max_hops": 3},
    )
    assert response.status_code == 200
    trace = response.json()["data"]
    assert trace["found"] is True
    assert trace["path"][0] == BTC_ADDRESS
    assert trace["path"][-1] == CP1
    assert trace["path_edges"]
    assert "shortest observed path" in trace["disclaimer"]


def test_trace_incoming_direction(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.post(
        "/api/graph/trace",
        json={"wallet_address": BTC_ADDRESS, "direction": "incoming", "max_hops": 3},
    )
    assert response.status_code == 200
    trace = response.json()["data"]
    levels = trace["levels"]
    assert levels and levels[0]["hop"] == 1
    senders = {a["address"] for a in levels[0]["addresses"]}
    assert any(a in (CP1, CP2) for a in senders)


def test_trace_unreachable_target(client, monkeypatch):
    _seed(client, monkeypatch)
    # CP2 only SENDS to BTC (never receives), so an outgoing trace to CP2 is unreachable.
    response = client.post(
        "/api/graph/trace",
        json={
            "wallet_address": BTC_ADDRESS,
            "direction": "outgoing",
            "target_address": CP2,
            "max_hops": 4,
        },
    )
    trace = response.json()["data"]
    assert trace["found"] is False
    assert trace["note"]


def test_trace_clean_wallet(client, monkeypatch):
    _seed(client, monkeypatch)
    response = client.post(
        "/api/graph/trace",
        json={"wallet_address": BTC_ADDRESS, "direction": "outgoing", "max_hops": 3},
    )
    trace = response.json()["data"]
    # Clean database: no threat records, so nothing is flagged.
    assert trace["suspicious_nodes"] == []
