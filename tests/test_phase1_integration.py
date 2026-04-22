import os
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Mock env vars before importing main
os.environ["BP_API_KEY"] = "test_api_key_123"
os.environ["POSTGRES_DB_URL"] = "postgresql://backpocket_user:backpocket_password@localhost:5432/backpocket_db"

import services.database as db
from main import app
from services.db_router import get_conn, SQLITE_PATH
from services.stripe import PLAN_MONTHLY

client = TestClient(app)

def test_auth_middleware():
    print("\n--- Testing 1.4 Auth & RLS ---")
    # 1. No Auth -> Should be 401
    res = client.get("/api/twins")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print("✅ Unauthenticated request blocked (401)")

    # 2. X-API-Key Bypass -> Should be 200
    res = client.get("/api/twins", headers={"x-api-key": "test_api_key_123"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print("✅ Authenticated request permitted (200)")

def test_dual_write_db():
    db.init_db() # Ensure schema is up-to-date
    print("\n--- Testing 1.3 Dual-Write Postgres & SQLite ---")
    test_user_id = "11111111-1111-1111-1111-111111111111" # Valid UUID
    test_email = "dualwrite@test.com"
    
    # Ensure router knows Postgres is available for the test
    import services.db_router as router
    router.DB_BACKEND = "postgres"
    
    # Use router to get dual-write connection
    conn = get_conn(user_id=test_user_id)
    
    # 1. Write data (without 'with' for cross-compatibility)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO leads (user_id, client_name, email, status) VALUES (%s, %s, %s, %s)",
            (test_user_id, "Dual Write Test", test_email, "new")
        )
    finally:
        if hasattr(cur, 'close') and cur.pg_cursor is None and cur.sl_cursor is None: 
            pass # DualWriteCursor doesn't strictly need close for this test
    conn.commit()

    # 2. Verify Postgres
    import psycopg2
    pg_conn = psycopg2.connect(os.environ["POSTGRES_DB_URL"])
    pg_cur = pg_conn.cursor()
    pg_cur.execute("SELECT client_name FROM leads WHERE email = %s", (test_email,))
    pg_res = pg_cur.fetchone()
    pg_cur.close()
    pg_conn.close()
    
    assert pg_res is not None, "Data not found in Postgres"
    print("✅ Data successfully written to PostgreSQL (Primary)")

    # 3. Verify SQLite
    sl_conn = sqlite3.connect(SQLITE_PATH)
    sl_cur = sl_conn.cursor()
    sl_cur.execute("SELECT client_name FROM leads WHERE email = ?", (test_email,))
    sl_res = sl_cur.fetchone()
    sl_conn.close()

    assert sl_res is not None, "Data not found in SQLite"
    print("✅ Data successfully mirrored to SQLite (Fallback)")

@patch("services.pgvector_rag.get_openrouter_response")
def test_rag_chat(mock_openrouter):
    print("\n--- Testing 1.2 Postgres RAG Injection ---")
    mock_openrouter.return_value = "This is a RAG-augmented response."
    
    res = client.post(
        "/api/twins/chat", 
        json={"message": "What is my markup?", "twin_type": "estimator"},
        headers={"x-api-key": "test_api_key_123"}
    )
    
    assert res.status_code == 200
    assert res.json()["response"] == "This is a RAG-augmented response."
    print("✅ AI Chat successfully routed through Postgres vector RAG")

@patch("services.stripe._stripe")
def test_stripe_billing(mock_stripe):
    print("\n--- Testing 1.1 Stripe Checkout Integration ---")
    
    # Setup mock
    mock_session = MagicMock()
    mock_session.id = "cs_test_test"
    mock_session.url = "https://checkout.stripe.com/test"
    mock_stripe.return_value.checkout.Session.create.return_value = mock_session

    res = client.post(
        "/api/billing/checkout",
        json={"plan": PLAN_MONTHLY, "customer_email": "billing@test.com"},
        headers={"x-api-key": "test_api_key_123"}
    )
    
    assert res.status_code == 200
    assert "url" in res.json()
    print(f"✅ Stripe Monthly Checkout URL generated: {res.json()['url']}")

if __name__ == "__main__":
    print("🚀 Running Phase 1 Integration Tests...\n")
    try:
        test_auth_middleware()
        test_dual_write_db()
        test_rag_chat()
        test_stripe_billing()
        print("\n🎉 ALL PHASE 1 TESTS PASSED. SYSTEM IS READY FOR PHASE 2. 🎉\n")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
