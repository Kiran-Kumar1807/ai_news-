"""Tests for the manual ingestion trigger endpoint."""
from backend.api.routes import admin
from ingestion.ingest import IngestResult


def test_ingest_disabled_when_no_admin_token(client, monkeypatch):
    monkeypatch.setattr(admin.settings, "admin_token", "")
    resp = client.post("/admin/ingest")
    assert resp.status_code == 503


def test_ingest_rejects_bad_token(client, monkeypatch):
    monkeypatch.setattr(admin.settings, "admin_token", "s3cret")
    resp = client.post("/admin/ingest", headers={"X-Admin-Token": "wrong"})
    assert resp.status_code == 401


def test_ingest_runs_with_valid_token(client, monkeypatch):
    monkeypatch.setattr(admin.settings, "admin_token", "s3cret")
    monkeypatch.setattr(
        admin, "run_ingestion", lambda: IngestResult(fetched=5, stored=3, duplicates=2)
    )
    resp = client.post("/admin/ingest", headers={"X-Admin-Token": "s3cret"})
    assert resp.status_code == 200
    assert resp.json() == {"fetched": 5, "stored": 3, "duplicates": 2}
