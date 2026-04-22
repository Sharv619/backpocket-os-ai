#!/usr/bin/env python3
"""
BackPocket OS - Test Suite
Run all demo path tests
"""

import requests
import sqlite3
import time
import os
import subprocess
import sys

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "backpocket.db"


def ensure_server():
    """Check if server is running, start if not"""
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ Server already running")
        return True
    except:
        print("🔄 Starting server...")
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(4)
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("✅ Server started")
            return True
        except:
            print("❌ Server failed to start")
            return False


def print_test(name, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")
    return status


def test_health():
    print("\n" + "=" * 50)
    print("TEST 1: Health & Status")
    print("=" * 50)

    r = requests.get(f"{BASE_URL}/health", timeout=5)
    data = r.json()
    print_test(
        "Health endpoint", r.status_code == 200, f"Version: {data.get('version')}"
    )
    print_test(
        "Pending refs",
        len(data.get("pending", [])) == 5,
        f"Count: {len(data.get('pending', []))}",
    )

    r = requests.get(f"{BASE_URL}/api/status", timeout=5)
    print_test("Status endpoint", r.status_code == 200)


def test_pending_emails():
    print("\n" + "=" * 50)
    print("TEST 2: Pending Emails (Mock Data)")
    print("=" * 50)

    r = requests.get(f"{BASE_URL}/api/pending", timeout=5)
    data = r.json()
    items = data.get("items", [])
    print_test("Pending API", r.status_code == 200, f"Items: {len(items)}")

    if items:
        print_test("Mock data present", len(items) == 5)
        for item in items[:2]:
            print(
                f"   - {item.get('ref_id')}: {item.get('subject', 'No subject')[:40]}"
            )

    r = requests.get(f"{BASE_URL}/api/drafts", timeout=5)
    print_test("Drafts endpoint", r.status_code == 200)

    if items:
        ref_id = items[0]["ref_id"]
        r = requests.get(f"{BASE_URL}/api/draft/{ref_id}", timeout=5)
        print_test(f"Draft detail ({ref_id})", r.status_code == 200)


def test_twin_chat():
    print("\n" + "=" * 50)
    print("TEST 3: Twin Chat")
    print("=" * 50)

    r = requests.get(f"{BASE_URL}/api/conversations", timeout=5)
    print_test("Conversations list", r.status_code == 200)

    payload = {"message": "hello", "twin_type": "estimator"}
    r = requests.post(f"{BASE_URL}/api/twins/chat", json=payload, timeout=30)
    if r.status_code == 200:
        print_test("Twin chat", True, "Response received")
    else:
        print_test(
            "Twin chat", False, f"Status: {r.status_code} - payload: {payload}"
        )


def test_documents():
    print("\n" + "=" * 50)
    print("TEST 4: Documents + AI")
    print("=" * 50)

    r = requests.get(f"{BASE_URL}/api/documents", timeout=5)
    data = r.json()
    print_test("Documents list", r.status_code == 200, f"Count: {data.get('count', 0)}")

    docs = data.get("documents", [])
    if docs:
        doc_id = docs[0]["id"]
        r = requests.post(f"{BASE_URL}/api/documents/analyze/{doc_id}", timeout=90)
        if r.status_code == 200:
            result = r.json()
            if result.get("status") == "success":
                print_test("Document analyze", True, "AI analysis completed")
            else:
                print_test("Document analyze", False, result.get("message", "Failed"))
        else:
            print_test("Document analyze", False, f"Status: {r.status_code}")
    else:
        print("   Skipping - no documents to analyze")


def test_database():
    print("\n" + "=" * 50)
    print("TEST 5: Database Validation")
    print("=" * 50)

    if not os.path.exists(DB_PATH):
        print_test("Database exists", False, "backpocket.db not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM pending_approvals")
    count = cursor.fetchone()[0]
    print_test("Pending approvals", count >= 5, f"Count: {count}")

    cursor.execute("SELECT COUNT(*) FROM instructions")
    count = cursor.fetchone()[0]
    print_test("Instructions", count >= 10, f"Count: {count}")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print_test("Tables exist", "pending_approvals" in tables)
    print_test("Documents table", "documents" in tables)

    conn.close()


def test_sheets():
    print("\n" + "=" * 50)
    print("TEST 6: Google Sheets")
    print("=" * 50)

    r = requests.get(f"{BASE_URL}/api/client-master", timeout=10)
    print_test("Client master", r.status_code == 200)


def main():
    print("🚀 Starting BackPocket OS Test Suite")
    print(f"   Server: {BASE_URL}")
    print(f"   Database: {DB_PATH}")

    if not ensure_server():
        print("❌ Could not start server. Exiting.")
        return

    try:
        test_health()
        test_pending_emails()
        test_twin_chat()
        test_documents()
        test_database()
        test_sheets()
    except Exception as e:
        print(f"\n❌ Test error: {e}")

    print("\n" + "=" * 50)
    print("✅ Test Suite Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
