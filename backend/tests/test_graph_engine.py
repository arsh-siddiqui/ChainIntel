"""Graph engine unit tests (hermetic, FakeProvider-backed)."""
from __future__ import annotations

from app.core.database import SessionLocal
from app.models import ThreatFinding
from app.services.graph_analysis import build_graph, trace_funds
from tests.fake_provider import BTC_ADDRESS, TXS, install_fake_provider


def _seed_txs(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")
    client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS})
    return SessionLocal()


def test_build_graph_aggregates_parallel_edges(client, monkeypatch):
    db = _seed_txs(client, monkeypatch)
    try:
        graph = build_graph(db, BTC_ADDRESS, hops=2)
        pairs = [(e["source"], e["target"]) for e in graph["edges"]]
        assert len(pairs) == len(set(pairs)), "parallel edges must be aggregated"
        assert graph["stats"]["unique_wallets"] == len(graph["nodes"])
    finally:
        db.close()


def test_build_graph_hops_bound(client, monkeypatch):
    _seed_txs(client, monkeypatch)
    db = SessionLocal()
    try:
        one_hop = build_graph(db, BTC_ADDRESS, hops=1)
        three_hop = build_graph(db, BTC_ADDRESS, hops=3)
        assert one_hop["stats"]["node_count"] <= three_hop["stats"]["node_count"]
        assert one_hop["stats"]["node_count"] >= 2
    finally:
        db.close()


def test_build_graph_max_nodes_limit(client, monkeypatch):
    _seed_txs(client, monkeypatch)
    db = SessionLocal()
    try:
        graph = build_graph(db, BTC_ADDRESS, hops=5, max_nodes=2)
        assert graph["stats"]["node_count"] <= 2
        assert graph["stats"]["truncated"] is True
    finally:
        db.close()


def test_node_risk_from_threat_records(client, monkeypatch):
    _seed_txs(client, monkeypatch)
    db = SessionLocal()
    try:
        finding = ThreatFinding(
            wallet_address="1HdS1CMasR6XMN4F5L8uLqEtduUV2uuD6C",
            blockchain="bitcoin",
            category="Ransomware",
            label="Fake Feed Record",
            source="Test Feed",
            confidence=0.9,
            status="IMPORTED",
        )
        db.add(finding)
        db.commit()
        graph = build_graph(db, BTC_ADDRESS, hops=2)
        by_id = {n["id"]: n for n in graph["nodes"]}
        flagged = by_id["1HdS1CMasR6XMN4F5L8uLqEtduUV2uuD6C"]
        assert flagged["risk"] == "high"
        assert flagged["type"] == "ransomware"
        assert by_id[BTC_ADDRESS]["focus"] is True
    finally:
        db.query(ThreatFinding).filter(ThreatFinding.source == "Test Feed").delete()
        db.commit()
        db.close()


def test_trace_bounded_hops(client, monkeypatch):
    _seed_txs(client, monkeypatch)
    db = SessionLocal()
    try:
        result = trace_funds(db, BTC_ADDRESS, direction="outgoing", max_hops=2)
        assert result["max_hops"] == 2
        assert all(level["hop"] <= 2 for level in result["levels"])
    finally:
        db.close()
