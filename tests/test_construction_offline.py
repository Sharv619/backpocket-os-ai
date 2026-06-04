import sqlite3

import pytest


@pytest.fixture()
def isolated_construction_db(tmp_path, monkeypatch):
    db_path = tmp_path / "construction.db"

    import services.database as db
    import services.construction as construction

    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    monkeypatch.setattr(construction, "DB_PATH", str(db_path))
    db.init_db()
    return construction.ConstructionManager(), str(db_path)


def test_create_lead_is_idempotent_by_client_action_id(isolated_construction_db):
    manager, db_path = isolated_construction_db

    first = manager.create_lead(
        client_name="Sarah Jones",
        email="",
        job_type="Kitchen Reno",
        location="Parramatta",
        urgency="high",
        budget=15000,
        client_action_id="offline-lead-001",
    )
    second = manager.create_lead(
        client_name="Sarah Jones",
        email="",
        job_type="Kitchen Reno",
        location="Parramatta",
        urgency="high",
        budget=15000,
        client_action_id="offline-lead-001",
    )

    assert first["lead_id"] == second["lead_id"]
    assert second["deduplicated"] is True

    con = sqlite3.connect(db_path)
    count = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    con.close()
    assert count == 1


def test_create_quote_and_payment_are_idempotent_by_client_action_id(
    isolated_construction_db,
):
    manager, db_path = isolated_construction_db

    lead = manager.create_lead(
        client_name="Ben Watts",
        email="ben@example.com",
        job_type="Deck Build",
        location="Penrith",
        urgency="medium",
        budget=12000,
        client_action_id="lead-002",
    )

    first_quote = manager.create_quote(
        lead_id=lead["lead_id"],
        materials_cost=4000,
        labor_cost=2500,
        markup_percent=20,
        client_action_id="quote-002",
    )
    second_quote = manager.create_quote(
        lead_id=lead["lead_id"],
        materials_cost=4000,
        labor_cost=2500,
        markup_percent=20,
        client_action_id="quote-002",
    )

    assert first_quote["quote_id"] == second_quote["quote_id"]
    assert second_quote["deduplicated"] is True

    first_payment = manager.record_payment(
        quote_id=first_quote["quote_id"],
        amount=1000,
        client_action_id="payment-002",
    )
    second_payment = manager.record_payment(
        quote_id=first_quote["quote_id"],
        amount=1000,
        client_action_id="payment-002",
    )

    assert first_payment["payment_id"] == second_payment["payment_id"]
    assert second_payment["deduplicated"] is True

    con = sqlite3.connect(db_path)
    quote_count = con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    payment_count = con.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    con.close()

    assert quote_count == 1
    assert payment_count == 1
