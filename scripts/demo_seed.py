"""
demo_seed.py — One-command demo reset for BackPocket OS hackathon demo.

Usage:
    python3 scripts/demo_seed.py

What it does:
  1. Wipes pending_approvals, action_history, processed_messages
  2. Seeds 5 realistic tradie emails (tier 1-5)
  3. Seeds 3 twin instructions
  4. Confirms everything looks correct
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime

DB_PATH = "backpocket.db"

MOCK_EMAILS = [
    {
        # Tier 1 — new tradie lead, needs a quote
        "ref_id": "DEMO-00001",
        "message_id": "demo_msg_001",
        "thread_id": "demo_thread_001",
        "sender": "steve.johnson@sparkypro.com.au",
        "subject": "Need a quote for rewire in Campbelltown",
        "draft_body": "Hi Steve,\n\nThanks for reaching out about the rewire job in Campbelltown. I'd love to get you a quote sorted. Can we lock in a quick onsite inspection this week? I'll send through a calendar invite once you confirm a time that suits.\n\nTalk soon, Steve",
        "delivered_to": "steve@backpocket.os",
        "tier": "1",
        "status": "pending",
    },
    {
        # Tier 1 — existing client, invoice query
        "ref_id": "DEMO-00002",
        "message_id": "demo_msg_002",
        "thread_id": "demo_thread_002",
        "sender": "mike.walsh@everflowplumbing.com.au",
        "subject": "Invoice for blocked drain - Job #4421",
        "draft_body": "Hi Mike,\n\nThank you for completing Job #4421 — the blocked drain at 14 Pemberton St. I've reviewed the invoice and everything looks correct. Payment will be processed within 2 business days. Really appreciate the quick turnaround.\n\nTalk soon, Steve",
        "delivered_to": "steve@backpocket.os",
        "tier": "1",
        "status": "pending",
    },
    {
        # Tier 3 — supplier quote
        "ref_id": "DEMO-00003",
        "message_id": "demo_msg_003",
        "thread_id": "demo_thread_003",
        "sender": "quotes@bunningsbusiness.com.au",
        "subject": "Trade Quote #BT-8821 — Cable & Conduit (Campbelltown job)",
        "draft_body": "Hi,\n\nThank you for the trade quote BT-8821. I've noted the cable and conduit pricing and will factor this into the client quote with our standard margin. I'll confirm the order once the client approves.\n\nThanks, Steve",
        "delivered_to": "steve@backpocket.os",
        "tier": "3",
        "status": "pending",
    },
    {
        # Tier 4 — ServiceM8 job digest
        "ref_id": "DEMO-00004",
        "message_id": "demo_msg_004",
        "thread_id": "demo_thread_004",
        "sender": "noreply@servicem8.com",
        "subject": "ServiceM8 Daily Digest — 3 jobs scheduled tomorrow",
        "draft_body": "Automated digest from ServiceM8. 3 jobs scheduled for tomorrow. No immediate action required — check the app for details.",
        "delivered_to": "steve@backpocket.os",
        "tier": "4",
        "status": "pending",
    },
    {
        # Tier 5 — spam
        "ref_id": "DEMO-00005",
        "message_id": "demo_msg_005",
        "thread_id": "demo_thread_005",
        "sender": "deals@promo-blast.com.au",
        "subject": "WIN a $5,000 BUNNINGS VOUCHER — Limited Time!!!",
        "draft_body": "SPAM — no response required.",
        "delivered_to": "steve@backpocket.os",
        "tier": "5",
        "status": "pending",
    },
]

MOCK_INSTRUCTIONS = [
    {
        "instruction_text": "Always respond in Steve's voice — direct, friendly, tradie-professional. Reference job numbers, dollar amounts and suburbs when available.",
        "category": "tone",
        "target": "all",
        "target_type": "global",
        "is_critical": 1,
        "is_test_mode": 0,
        "is_active": 1,
    },
    {
        "instruction_text": "For new leads requesting a quote (Tier 1), always offer an onsite inspection and send a calendar invite. Apply a 30% margin when generating client quotes.",
        "category": "priority",
        "target": "all",
        "target_type": "global",
        "is_critical": 1,
        "is_test_mode": 0,
        "is_active": 1,
    },
    {
        "instruction_text": "After every completed job, request a Google review from the client and issue a lifetime warranty document. Never skip these steps.",
        "category": "workflow",
        "target": "all",
        "target_type": "global",
        "is_critical": 1,
        "is_test_mode": 0,
        "is_active": 1,
    },
]


def reset_demo():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Resetting demo data...")

    cur.execute("DELETE FROM pending_approvals WHERE ref_id LIKE 'DEMO-%' OR ref_id LIKE '2026-%'")
    cur.execute("DELETE FROM processed_messages WHERE message_id LIKE 'demo_%'")
    cur.execute("DELETE FROM action_history WHERE ref_id LIKE 'DEMO-%'")
    print("   Cleared old demo rows")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for email in MOCK_EMAILS:
        cur.execute(
            """INSERT OR REPLACE INTO pending_approvals
               (ref_id, message_id, thread_id, sender, subject, draft_body,
                delivered_to, tier, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email["ref_id"], email["message_id"], email["thread_id"],
                email["sender"], email["subject"], email["draft_body"],
                email["delivered_to"], email["tier"], email["status"], now,
            ),
        )
    print(f"   Seeded {len(MOCK_EMAILS)} tradie demo emails")

    cur.execute("SELECT COUNT(*) FROM instructions")
    if cur.fetchone()[0] == 0:
        for inst in MOCK_INSTRUCTIONS:
            cur.execute(
                """INSERT INTO instructions
                   (instruction_text, category, target, target_type,
                    is_critical, is_test_mode, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    inst["instruction_text"], inst["category"], inst["target"],
                    inst["target_type"], inst["is_critical"],
                    inst["is_test_mode"], inst["is_active"],
                ),
            )
        print(f"   Seeded {len(MOCK_INSTRUCTIONS)} twin instructions")
    else:
        print("   Instructions already exist — skipped")

    conn.commit()
    conn.close()

    conn2 = sqlite3.connect(DB_PATH)
    cur2 = conn2.cursor()
    cur2.execute("SELECT ref_id, tier, sender FROM pending_approvals ORDER BY tier")
    rows = cur2.fetchall()
    conn2.close()

    print("\nDemo inbox:")
    TIER_LABELS = ["", "URGENT", "HIGH", "MEDIUM", "LOW", "SPAM"]
    for r in rows:
        tier_label = TIER_LABELS[int(r[1])] if int(r[1]) < len(TIER_LABELS) else "?"
        print(f"   [{r[1]}] {tier_label:6s} — {r[0]} — {r[2]}")

    print("\nDemo ready! Start the server:")
    print("   python3 -m uvicorn main:app --host 127.0.0.1 --port 8000")
    print("   Open: http://127.0.0.1:8000/static/index.html")


if __name__ == "__main__":
    reset_demo()
