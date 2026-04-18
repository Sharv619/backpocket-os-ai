#!/usr/bin/env python3
"""
Seed ChromaDB RAG from existing BackPocket data.
Sources: pending_approvals (drafts), corrections, instructions, leads+quotes.
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.twin_engine import RAGContextBuilder, TwinType

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backpocket.db")


def seed():
    rag = RAGContextBuilder()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    total = 0

    # 1. Seed from pending_approvals (email drafts)
    print("── Seeding email drafts ──")
    cur.execute(
        "SELECT ref_id, sender, subject, draft_body, tier "
        "FROM pending_approvals WHERE draft_body IS NOT NULL AND LENGTH(draft_body) > 20"
    )
    for row in cur.fetchall():
        doc_id = f"draft-{row['ref_id']}"
        text = (
            f"Email from: {row['sender']}\n"
            f"Subject: {row['subject']}\n"
            f"Tier: {row['tier']}\n"
            f"AI Draft Response:\n{row['draft_body']}"
        )
        meta = {
            "source": "email_draft",
            "ref_id": row["ref_id"],
            "sender": row["sender"] or "",
            "subject": row["subject"] or "",
            "tier": str(row["tier"]),
        }
        ok = rag.ingest(TwinType.ADMIN, doc_id, text, meta)
        if ok:
            total += 1
            print(f"  + {doc_id}: {row['sender'][:30]} — {row['subject'][:40]}")

    # 2. Seed from corrections (learned patterns)
    print("\n── Seeding corrections ──")
    cur.execute(
        "SELECT id, ref_id, correction_type, sender, subject, "
        "original_draft, corrected_draft, feedback "
        "FROM corrections WHERE corrected_draft IS NOT NULL AND LENGTH(corrected_draft) > 20"
    )
    for row in cur.fetchall():
        doc_id = f"correction-{row['id']}"
        text = (
            f"Correction ({row['correction_type']}):\n"
            f"Sender: {row['sender']}\nSubject: {row['subject']}\n"
            f"Original: {row['original_draft']}\n"
            f"Corrected: {row['corrected_draft']}\n"
            f"Feedback: {row['feedback']}"
        )
        meta = {
            "source": "correction",
            "ref_id": row["ref_id"] or "",
            "correction_type": row["correction_type"] or "",
            "feedback": row["feedback"] or "",
        }
        twin = TwinType.AUDITOR if "review" in (row["feedback"] or "").lower() else TwinType.ADMIN
        ok = rag.ingest(twin, doc_id, text, meta)
        if ok:
            total += 1
            print(f"  + {doc_id}: {row['correction_type']} — {row['feedback'][:40]}")

    # 3. Seed from instructions (business rules)
    print("\n── Seeding instructions ──")
    cur.execute("SELECT id, instruction_text, category FROM instructions WHERE is_active = 1")
    for row in cur.fetchall():
        doc_id = f"instruction-{row['id']}"
        text = f"Business Rule [{row['category']}]: {row['instruction_text']}"
        meta = {
            "source": "instruction",
            "category": row["category"] or "general",
        }
        ok = rag.ingest(TwinType.ADMIN, doc_id, text, meta)
        if ok:
            total += 1
            print(f"  + {doc_id}: [{row['category']}] {row['instruction_text'][:50]}")

    # 4. Seed from leads + quotes (business context)
    print("\n── Seeding construction data ──")
    cur.execute(
        "SELECT l.id, l.client_name, l.job_type, l.location, l.urgency, l.estimated_budget, "
        "q.materials_cost, q.labor_cost, q.markup_percent, q.total_amount, q.status as q_status "
        "FROM leads l LEFT JOIN quotes q ON q.lead_id = l.id"
    )
    for row in cur.fetchall():
        doc_id = f"lead-{row['id']}"
        text = (
            f"Client: {row['client_name']}, Job: {row['job_type']}, Location: {row['location']}, "
            f"Urgency: {row['urgency']}, Budget: ${row['estimated_budget'] or 'TBD'}"
        )
        if row["materials_cost"]:
            text += (
                f"\nQuote: materials ${row['materials_cost']}, labor ${row['labor_cost']}, "
                f"markup {row['markup_percent']}%, total ${row['total_amount']} ({row['q_status']})"
            )
        meta = {
            "source": "construction",
            "client": row["client_name"] or "",
            "job_type": row["job_type"] or "",
            "location": row["location"] or "",
        }
        ok = rag.ingest(TwinType.ACCOUNTANT, doc_id, text, meta)
        if ok:
            total += 1
            print(f"  + {doc_id}: {row['client_name']} — {row['job_type']} @ {row['location']}")

    # 5. Seed from action_history (what user actually did)
    print("\n── Seeding action history ──")
    cur.execute(
        "SELECT ah.id, ah.ref_id, ah.action, ah.tier, ah.notes, "
        "pa.sender, pa.subject "
        "FROM action_history ah "
        "LEFT JOIN pending_approvals pa ON pa.ref_id = ah.ref_id "
        "WHERE ah.action IN ('approved', 'approved_demo', 'revised', 'archived')"
    )
    for row in cur.fetchall():
        doc_id = f"action-{row['id']}"
        text = (
            f"User action: {row['action']} on {row['ref_id']}\n"
            f"Sender: {row['sender'] or 'unknown'}, Subject: {row['subject'] or 'unknown'}\n"
            f"Tier: {row['tier']}, Notes: {row['notes'] or 'none'}"
        )
        meta = {
            "source": "action_history",
            "action": row["action"] or "",
            "ref_id": row["ref_id"] or "",
        }
        ok = rag.ingest(TwinType.ADMIN, doc_id, text, meta)
        if ok:
            total += 1
            print(f"  + {doc_id}: {row['action']} — {row['ref_id']}")

    conn.close()
    print(f"\n{'='*50}")
    print(f"RAG SEEDED: {total} documents ingested into ChromaDB")
    print(f"ChromaDB path: {os.path.expanduser('~/.backpocket/chromadb/')}")


if __name__ == "__main__":
    seed()
