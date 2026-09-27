"""Health and envelope tests."""
from __future__ import annotations


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["status"] in ("healthy", "degraded")
    assert body["data"]["mode"] == "LIVE"


def test_api_root(client):
    response = client.get("/api")
    assert response.status_code == 200
    assert response.json()["data"]["docs"] == "/docs"


def test_unknown_route_returns_envelope_error(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "HTTP_ERROR"
