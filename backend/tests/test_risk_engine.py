"""Risk engine unit tests."""
from __future__ import annotations

from app.services.risk_engine import DISCLAIMER, assess


def _ctx(**overrides):
    base = {
        "focus_address": "DEMO-TEST-0001",
        "transactions": [],
        "threat_findings": [],
        "counterparty_threats": [],
        "graph_stats": {},
        "osint_findings": [],
    }
    base.update(overrides)
    return base


def test_clean_wallet_is_low():
    result = assess(_ctx())
    assert result["band"] == "LOW"
    assert result["score"] == 0
    assert all(i["status"] == "NOT_TRIGGERED" for i in result["indicators"])
    assert result["disclaimer"] == DISCLAIMER


def test_direct_threat_match_weights_40():
    result = assess(
        _ctx(
            threat_findings=[
                {"category": "Ransomware", "label": "X (Simulated)", "source": "Feed", "confidence": 0.9, "reference_url": "https://example.org"}
            ]
        )
    )
    assert result["score"] >= 40
    assert result["band"] in ("MODERATE", "ELEVATED", "HIGH")
    match = next(i for i in result["indicators"] if i["name"] == "Threat intelligence match")
    assert match["status"] == "TRIGGERED"
    assert "Feed" in match["evidence"]


def test_high_severity_category_upgrades_band():
    result = assess(
        _ctx(
            threat_findings=[
                {"category": "Ransomware", "label": "X (Simulated)", "source": "Feed", "confidence": 0.9}
            ],
            graph_stats={"unique_wallets": 6, "edge_count": 9},
        )
    )
    # 40 + 10 (multiple intermediaries) = 50 -> normally MODERATE, upgraded to ELEVATED.
    assert result["band"] == "ELEVATED"


def test_counterparty_and_mixer_indicators():
    result = assess(
        _ctx(
            counterparty_threats=[
                {"wallet_address": "DEMO-OTHER-0001", "category": "Suspicious Service", "label": "Mixer", "source": "Feed", "confidence": 0.8}
            ]
        )
    )
    names = {i["name"]: i["status"] for i in result["indicators"]}
    assert names["High-risk counterparty"] == "TRIGGERED"
    assert names["Mixer/service interaction"] == "TRIGGERED"
    assert result["score"] >= 30


def test_rapid_movement_detection():
    txs = [
        {"from_address": "DEMO-TEST-0001", "to_address": "DEMO-X", "amount": 1.0, "timestamp": f"2026-01-01T10:0{i}:00Z"}
        for i in range(4)
    ]
    result = assess(_ctx(transactions=txs))
    rapid = next(i for i in result["indicators"] if i["name"] == "Rapid fund movement")
    assert rapid["status"] == "TRIGGERED"


def test_fragmentation_detection():
    txs = [
        {"from_address": "DEMO-TEST-0001", "to_address": "DEMO-TARGET", "amount": 0.1, "timestamp": "2026-01-01T10:00:00Z"}
        for _ in range(6)
    ]
    result = assess(_ctx(transactions=txs))
    frag = next(i for i in result["indicators"] if i["name"] == "Transaction fragmentation")
    assert frag["status"] == "TRIGGERED"


def test_osint_reputation_indicator():
    result = assess(
        _ctx(
            osint_findings=[
                {"status": "FOUND", "confidence": 0.85, "source": "DemoScamDB (Simulated)", "finding": "Reported (simulated)"}
            ]
        )
    )
    rep = next(i for i in result["indicators"] if i["name"] == "External reputation match")
    assert rep["status"] == "TRIGGERED"


def test_indicators_are_explainable():
    result = assess(_ctx(graph_stats={"unique_wallets": 10, "edge_count": 12}))
    for indicator in result["indicators"]:
        assert indicator["evidence"]  # every indicator carries evidence text
        assert indicator["description"]
        assert indicator["source"]
        assert isinstance(indicator["weight"], int)
