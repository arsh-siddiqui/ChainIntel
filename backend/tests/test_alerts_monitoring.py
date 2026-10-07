"""Monitoring and alert tests (live-only; alert lifecycle via rule evaluation)."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models import Alert
from app.services.alert_engine import evaluate_rules
from tests.fake_provider import BTC_ADDRESS, install_fake_provider


def _alert(wallet: str = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa") -> Alert:
    return Alert(
        wallet_address=wallet,
        rule={"direction": "any"},
        transaction_hash=f"tx-{datetime.utcnow().timestamp()}",
        severity="HIGH",
        status="NEW",
        title="Monitoring alert",
        message="Live monitoring event: outgoing transaction 2.0 BTC.",
        is_demo=False,
    )


def test_create_monitor_and_lifecycle(client):
    response = client.post(
        "/api/alerts/monitor",
        json={
            "wallet_address": BTC_ADDRESS,
            "blockchain": "bitcoin",
            "label": "Test monitor",
            "rules": {"direction": "incoming", "amount_threshold": 0.5},
        },
    )
    assert response.status_code == 200
    monitor = response.json()["data"]
    assert monitor["status"] == "ACTIVE"
    assert monitor["is_demo"] is False

    response = client.patch(f"/api/alerts/monitors/{monitor['id']}", json={"status": "PAUSED"})
    assert response.json()["data"]["status"] == "PAUSED"

    # Duplicate monitor rejected
    response = client.post("/api/alerts/monitor", json={"wallet_address": BTC_ADDRESS, "rules": {}})
    assert response.status_code == 409

    # Delete cleanup
    assert client.delete(f"/api/alerts/monitors/{monitor['id']}").status_code == 200


def test_monitor_invalid_address(client):
    response = client.post("/api/alerts/monitor", json={"wallet_address": "bad-address", "rules": {}})
    assert response.status_code == 400


def test_monitor_rejects_demo_address(client):
    response = client.post("/api/alerts/monitor", json={"wallet_address": "DEMO-ANY-0001", "rules": {}})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_WALLET"


def test_alert_status_lifecycle(client, db_session):
    alert = _alert()
    db_session.add(alert)
    db_session.commit()

    for status in ("ACKNOWLEDGED", "INVESTIGATING", "RESOLVED"):
        response = client.patch(f"/api/alerts/{alert.id}", json={"status": status})
        assert response.status_code == 200
        assert response.json()["data"]["status"] == status


def test_simulate_endpoint_removed(client):
    """The demo simulation endpoint no longer exists in live-only mode."""
    response = client.post("/api/alerts/simulate", json={"wallet_address": BTC_ADDRESS})
    assert response.status_code in (404, 405)


def test_rule_evaluation_thresholds():
    monitor_rules = {"direction": "outgoing", "amount_threshold": 1.0}
    now = datetime.utcnow()
    outgoing_tx = {
        "tx_hash": "rule-tx-1",
        "from_address": BTC_ADDRESS,
        "to_address": "1DV391rtxMcjofZWfmQGaDpcEQDxmRF8sd",
        "amount": 2.0,
        "asset": "BTC",
        "timestamp": now,
        "direction": "outgoing",
    }
    triggered, severity, reason = evaluate_rules(monitor_rules, outgoing_tx, BTC_ADDRESS, False, False)
    assert triggered is True
    assert severity in ("MEDIUM", "HIGH")

    below_threshold = dict(outgoing_tx, amount=0.5)
    triggered, _, _ = evaluate_rules(monitor_rules, below_threshold, BTC_ADDRESS, False, False)
    assert triggered is False


def test_rule_evaluation_threat_match_and_flagged_counterparty():
    """Test threat match and flagged counterparty rule triggers."""
    rules_threat = {"direction": "any", "on_threat_match": True}
    tx_any = {"tx_hash": "tx-threat-1", "from_address": BTC_ADDRESS, "to_address": "0x1234", "amount": 0.1, "asset": "ETH"}
    
    # Threat match on focus wallet triggers CRITICAL alert
    triggered, severity, reason = evaluate_rules(rules_threat, tx_any, BTC_ADDRESS, threat_match=True, flagged_counterparty=False)
    assert triggered is True
    assert severity == "CRITICAL"
    assert "threat-intelligence" in reason

    rules_counterparty = {"direction": "any", "flagged_counterparty": True}
    # Flagged counterparty triggers HIGH alert
    triggered, severity, reason = evaluate_rules(rules_counterparty, tx_any, BTC_ADDRESS, threat_match=False, flagged_counterparty=True)
    assert triggered is True
    assert severity == "HIGH"
    assert "counterparty" in reason


def test_alert_list_search_and_severity_filters(client, db_session):
    """Test /api/alerts listing with status and pagination filters."""
    a1 = _alert(wallet="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    a1.severity = "CRITICAL"
    a1.status = "NEW"
    
    a2 = _alert(wallet="bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr")
    a2.severity = "LOW"
    a2.status = "RESOLVED"

    db_session.add_all([a1, a2])
    db_session.commit()

    # Query all alerts
    response = client.get("/api/alerts")
    assert response.status_code == 200
    res = response.json()
    assert len(res["data"]) >= 2

    # Query by status=NEW
    response = client.get("/api/alerts?status=NEW")
    assert response.status_code == 200
    data_new = response.json()["data"]
    assert all(item["status"] == "NEW" for item in data_new)


def test_monitored_wallets_list_endpoint(client):
    """Test fetching monitored wallets list."""
    response = client.get("/api/alerts/monitors")
    assert response.status_code == 200
    monitors = response.json()["data"]
    assert isinstance(monitors, list)

