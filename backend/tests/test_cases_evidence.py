"""Case and evidence tests (hermetic, FakeProvider-backed)."""
from __future__ import annotations

from tests.fake_provider import BTC_ADDRESS, install_fake_provider


def test_case_lifecycle(client, monkeypatch):
    install_fake_provider(monkeypatch, "bitcoin")

    response = client.post(
        "/api/cases",
        json={"title": "Test Investigation Case", "description": "Created by automated test.", "priority": "HIGH"},
    )
    assert response.status_code == 200
    case = response.json()["data"]
    case_id = case["id"]
    assert case["case_number"].startswith("CASE-")
    assert case["status"] == "OPEN"
    assert any(e["event_type"] == "case_created" for e in case["timeline"])

    response = client.patch(f"/api/cases/{case_id}", json={"status": "UNDER_INVESTIGATION", "priority": "CRITICAL"})
    updated = response.json()["data"]
    assert updated["status"] == "UNDER_INVESTIGATION"
    assert updated["priority"] == "CRITICAL"
    assert any(e["event_type"] == "status_changed" for e in updated["timeline"])

    # Link an investigation (runs the pipeline through the FakeProvider).
    response = client.post(f"/api/cases/{case_id}/investigations", json={"wallet_address": BTC_ADDRESS})
    assert response.status_code == 200
    assert response.json()["data"]["investigation_id"]

    detail = client.get(f"/api/cases/{case_id}").json()["data"]
    assert len(detail["investigations"]) == 1
    assert any(e["event_type"] == "wallet_added" for e in detail["timeline"])

    response = client.post(f"/api/cases/{case_id}/notes", json={"note": "Analyst: reviewed timeline."})
    assert response.status_code == 200
    detail = client.get(f"/api/cases/{case_id}").json()["data"]
    assert any(e["event_type"] == "analyst_note" for e in detail["timeline"])


def test_case_not_found(client):
    response = client.get("/api/cases/999999")
    assert response.status_code == 404


def test_evidence_upload_note_and_file(client):
    case_id = client.post("/api/cases", json={"title": "Evidence Test Case"}).json()["data"]["id"]

    # Text evidence (analyst note style)
    response = client.post(
        f"/api/cases/{case_id}/evidence",
        data={"title": "Analyst observation", "evidence_type": "Analyst Note", "content_text": "Transaction chain reviewed."},
    )
    assert response.status_code == 200
    note = response.json()["data"]
    assert len(note["sha256"]) == 64
    assert note["has_file"] is False

    # File evidence
    response = client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("screenshot.txt", b"chainintel-evidence-bytes", "text/plain")},
        data={"title": "Captured response", "evidence_type": "API Response", "description": "Test artifact"},
    )
    assert response.status_code == 200
    file_evidence = response.json()["data"]
    assert file_evidence["has_file"] is True
    assert file_evidence["size_bytes"] > 0

    detail = client.get(f"/api/cases/{case_id}").json()["data"]
    assert len(detail["evidence"]) == 2
    assert any(e["event_type"] == "evidence_attached" for e in detail["timeline"])

    listing = client.get("/api/evidence?search=Captured").json()["data"]
    assert listing and listing[0]["sha256"]

    single = client.get(f"/api/evidence/{file_evidence['id']}").json()["data"]
    assert single["integrity_verified"] is True

    download = client.get(f"/api/evidence/{file_evidence['id']}/download")
    assert download.status_code == 200
    assert download.content == b"chainintel-evidence-bytes"


def test_evidence_rejects_disallowed_extension(client):
    case_id = client.post("/api/cases", json={"title": "Bad File Case"}).json()["data"]["id"]
    response = client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
        data={"title": "Executable upload"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
