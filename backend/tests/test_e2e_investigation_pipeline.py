"""End-to-end integration tests for the full ChainIntel forensic investigation pipeline."""
from __future__ import annotations

import pytest
from tests.fake_provider import BTC_ADDRESS, install_fake_provider


def test_full_e2e_investigation_pipeline(client, monkeypatch):
    """Execute end-to-end workflow: wallet lookup -> risk -> graph -> OSINT -> case -> evidence -> report."""
    install_fake_provider(monkeypatch, "bitcoin")

    # Step 1: Target Wallet Investigation
    inv_response = client.post("/api/wallets/investigate", json={"address": BTC_ADDRESS})
    assert inv_response.status_code == 200
    bundle = inv_response.json()["data"]
    assert bundle["wallet"]["address"] == BTC_ADDRESS
    assert bundle["wallet"]["blockchain"] == "bitcoin"
    assert bundle["risk"]["score"] >= 0.0
    assert bundle["graph"]["nodes"]

    # Step 2: Wallet Details Endpoint
    wallet_response = client.get(f"/api/wallets/{BTC_ADDRESS}")
    assert wallet_response.status_code == 200
    wallet_data = wallet_response.json()["data"]
    assert wallet_data["validation"]["valid"] is True
    assert wallet_data["wallet"]["address"] == BTC_ADDRESS

    # Step 3: Multi-Hop Graph Traversal
    graph_response = client.get(f"/api/wallets/{BTC_ADDRESS}/graph?hops=3")
    assert graph_response.status_code == 200
    graph = graph_response.json()["data"]
    assert graph["stats"]["node_count"] >= 1
    assert graph["stats"]["edge_count"] >= 0

    # Step 4: Fund-Flow Path Tracing
    trace_response = client.post(
        "/api/graph/trace",
        json={"wallet_address": BTC_ADDRESS, "direction": "outgoing", "max_hops": 3},
    )
    assert trace_response.status_code == 200
    trace = trace_response.json()["data"]
    assert "disclaimer" in trace
    assert "path_edges" in trace or "suspicious_nodes" in trace

    # Step 5: OSINT Correlation
    osint_response = client.get(f"/api/osint/search/{BTC_ADDRESS}")
    assert osint_response.status_code == 200
    osint = osint_response.json()["data"]
    assert osint["validation"]["valid"] is True
    assert osint["correlation"]["provider_count"] >= 5

    # Step 6: Case Creation
    case_response = client.post(
        "/api/cases",
        json={
            "title": "E2E Automated Investigation Case",
            "description": "Full pipeline automated verification.",
            "priority": "HIGH",
        },
    )
    assert case_response.status_code == 200
    case_data = case_response.json()["data"]
    case_id = case_data["id"]
    assert case_data["case_number"].startswith("CASE-")

    # Link investigation to case
    link_response = client.post(
        f"/api/cases/{case_id}/investigations",
        json={"wallet_address": BTC_ADDRESS},
    )
    assert link_response.status_code == 200

    # Step 7: Evidence Attachment & SHA-256 Verification
    evidence_response = client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("investigation_graph_snapshot.json", b'{"nodes": [], "edges": []}', "application/json")},
        data={"title": "Graph Snapshot Artifact", "evidence_type": "Graph Snapshot", "description": "E2E test artifact"},
    )
    assert evidence_response.status_code == 200
    evidence = evidence_response.json()["data"]
    assert evidence["sha256"]
    assert len(evidence["sha256"]) == 64

    # Verify Evidence Integrity
    verify_response = client.get(f"/api/evidence/{evidence['id']}")
    assert verify_response.status_code == 200
    assert verify_response.json()["data"]["integrity_verified"] is True

    # Step 8: Forensic Report Generation
    report_response = client.post(
        "/api/reports/generate",
        json={"wallet_address": BTC_ADDRESS, "case_id": case_id, "title": "E2E Forensic Investigation Report"},
    )
    assert report_response.status_code == 200
    report = report_response.json()["data"]
    assert report["id"]
    assert report["wallet_address"] == BTC_ADDRESS

    # Fetch Report Detail
    detail_response = client.get(f"/api/reports/{report['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["title"] == "E2E Forensic Investigation Report"
