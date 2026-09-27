"""Report generation tests (hermetic, FakeProvider-backed)."""
from __future__ import annotations

import json

from tests.fake_provider import BTC_ADDRESS, install_fake_provider


def test_generate_and_download_report(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")
    response = client.post("/api/reports/generate", json={"wallet_address": BTC_ADDRESS})
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["id"]
    assert report["mode"] == "LIVE"
    payload = report["payload"]
    for section in ("wallet_summary", "transactions", "threat_findings", "osint_findings", "risk_indicators", "fund_flow", "disclaimers"):
        assert section in payload
    assert any("independently validated" in d for d in payload["disclaimers"])

    report_id = report["id"]

    pdf = client.get(f"/api/reports/{report_id}/download?format=pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:5] == b"%PDF-"

    json_download = client.get(f"/api/reports/{report_id}/download?format=json")
    parsed = json.loads(json_download.content)
    assert parsed["report_id"] == report_id

    csv_download = client.get(f"/api/reports/{report_id}/download?format=csv")
    assert csv_download.headers["content-type"].startswith("text/csv")
    header_line = csv_download.content.decode().splitlines()[0]
    assert "tx_hash" in header_line


def test_report_for_case_with_investigation(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")
    case_id = client.post("/api/cases", json={"title": "Report Case"}).json()["data"]["id"]
    client.post(f"/api/cases/{case_id}/investigations", json={"wallet_address": BTC_ADDRESS})
    response = client.post("/api/reports/generate", json={"case_id": case_id})
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["payload"]["case"]["id"] == case_id
    timeline = report["payload"]["timeline"]
    assert timeline


def test_report_requires_wallet_or_case(client):
    response = client.post("/api/reports/generate", json={})
    assert response.status_code == 400


def test_report_404(client):
    assert client.get("/api/reports/nope/download").status_code == 404
