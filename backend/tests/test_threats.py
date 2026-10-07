"""Threat intelligence tests (live-only; data via API import)."""
from __future__ import annotations

import json

CSV_CONTENT = """address,blockchain,label,category,source,reference_url,confidence,first_seen,last_seen,notes
1DDYrMcWpG3u7u33Tp2bGVsdAidgUehDCb,bitcoin,Test BTC Label,Scam,Test Feed,https://example.org/test,0.50,2026-01-01,2026-02-01,Test note
0x0000000000000000000000000000000000000001,ethereum,Test EVM Label,Fraud,Test Feed,,0.40,,,EVM record
NOT-A-VALID-ADDRESS,,Bad Record,Scam,Test Feed,,0.9,,,invalid address row
1DDYrMcWpG3u7u33Tp2bGVsdAidgUehDCb,bitcoin,Test BTC Label,Scam,Test Feed,,0.5,,,dup
"""


def _seed(client):
    files = {"file": ("threats.csv", CSV_CONTENT.encode("utf-8"), "text/csv")}
    response = client.post("/api/threats/import", files=files)
    assert response.status_code == 200
    return response.json()["data"]


def test_import_csv_with_validation(client):
    stats = _seed(client)
    assert stats["received"] == 4
    assert stats["valid"] == 2
    assert stats["invalid"] == 1
    assert stats["inserted"] == 2
    assert any("row 3" in error for error in stats["errors"])

    # Re-import: rows 1/2 update; row 4 is an in-batch duplicate.
    files = {"file": ("threats.csv", CSV_CONTENT.encode("utf-8"), "text/csv")}
    stats = client.post("/api/threats/import", files=files).json()["data"]
    assert stats["updated"] == 2
    assert stats["duplicates"] == 1


def test_import_rejects_demo_addresses(client):
    payload = [
        {
            "address": "DEMO-JSON-0001",
            "blockchain": "demo",
            "label": "Simulated Import",
            "category": "phishing",
            "source": "Test Feed",
            "confidence": 0.6,
        }
    ]
    files = {"file": ("threats.json", json.dumps(payload).encode(), "application/json")}
    stats = client.post("/api/threats/import", files=files).json()["data"]
    assert stats["inserted"] == 0
    assert stats["invalid"] == 1
    assert any("DEMO-" in error for error in stats["errors"])


def test_list_and_filter(client):
    _seed(client)
    response = client.get("/api/threats?page_size=50")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] >= 2
    item = body["data"][0]
    assert {"wallet_address", "category", "label", "source", "confidence", "reference_url"} <= set(item)

    response = client.get("/api/threats?category=Scam")
    assert all(t["category"] == "Scam" for t in response.json()["data"])


def test_threat_stats(client):
    _seed(client)
    data = client.get("/api/threats/stats").json()["data"]
    assert data["total"] >= 2
    assert data["flagged_wallets"] >= 2
    assert data["allowed_categories"]


def test_import_json_alias_normalization(client):
    payload = [
        {
            "address": "0x1111111111111111111111111111111111111111",
            "blockchain": "ethereum",
            "label": "JSON Import",
            "category": "phishing",
            "source": "Test Feed",
            "confidence": 0.6,
        }
    ]
    files = {"file": ("threats.json", json.dumps(payload).encode(), "application/json")}
    stats = client.post("/api/threats/import", files=files).json()["data"]
    assert stats["inserted"] == 1

    listing = client.get("/api/threats?search=0x1111111111111111111111111111111111111111").json()["data"]
    assert listing[0]["category"] == "Phishing"


def test_import_rejects_bad_format(client):
    files = {"file": ("threats.txt", b"hello", "text/plain")}
    response = client.post("/api/threats/import", files=files)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IMPORT_FORMAT_ERROR"


def test_threat_matching_known_entities(client):
    """Test known entities threat match resolution."""
    response = client.get("/api/threats?search=0x12d6621e19a95080e0276664261065623b1a0623")
    assert response.status_code == 200
    findings = response.json()["data"]
    assert any("Tornado" in f["label"] or f["category"] in ("Suspicious Service", "Mixer") for f in findings)

