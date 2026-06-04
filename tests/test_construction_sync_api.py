import asyncio
import sqlite3

import pytest
from routes.construction import create_lead


@pytest.fixture()
def isolated_construction_api(tmp_path, monkeypatch):
    db_path = tmp_path / "construction_api.db"

    import services.database as db
    import services.construction as construction

    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    monkeypatch.setattr(construction, "DB_PATH", str(db_path))
    monkeypatch.setattr(construction, "_manager", None)
    db.init_db()

    yield str(db_path)


def test_mobile_sync_replay_is_idempotent_for_lead_create(isolated_construction_api):
    db_path = isolated_construction_api
    payload = {
        "client_name": "Sarah Jones",
        "job_type": "Kitchen Reno",
        "location": "Parramatta",
        "estimated_budget": 15000,
        "urgency": "high",
        "client_action_id": "offline-lead-sync-001",
    }

    first_body = asyncio.run(create_lead(payload))
    second_body = asyncio.run(create_lead(payload))

    assert first_body["status"] == "success"
    assert second_body["status"] == "success"
    assert first_body["lead_id"] == second_body["lead_id"]
    assert first_body["client_action_id"] == payload["client_action_id"]
    assert second_body["client_action_id"] == payload["client_action_id"]
    assert second_body["data"]["deduplicated"] is True

    con = sqlite3.connect(db_path)
    count = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    row = con.execute(
        "SELECT client_action_id, email FROM leads WHERE id = ?",
        (first_body["lead_id"],),
    ).fetchone()
    con.close()

    assert count == 1
    assert row[0] == payload["client_action_id"]
    assert row[1] == "sarah-jones@backpocket.local"


def test_mobile_sync_validation_error_returns_error_status_and_no_lead_id(
    isolated_construction_api,
):
    db_path = isolated_construction_api
    payload = {
        "client_name": "Broken Payload",
        "job_type": "Deck Build",
        "estimated_budget": 12000,
        "client_action_id": "offline-lead-sync-invalid",
    }

    body = asyncio.run(create_lead(payload))
    assert body["status"] == "error"
    assert "location" in body["message"]
    assert "lead_id" not in body

    con = sqlite3.connect(db_path)
    count = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    con.close()
    assert count == 0
