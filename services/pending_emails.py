"""Shared helpers for pending mobile inbox snapshots."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

import services.database as db

_TIER_LABELS = {
    "1": "URGENT",
    "2": "HIGH",
    "3": "MEDIUM",
    "4": "LOW",
    "5": "SPAM",
}


def list_pending_email_items(limit: Optional[int] = None) -> list[dict]:
    """Return pending inbox items in the mobile-friendly shape."""
    conn = sqlite3.connect(db.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = (
        "SELECT ref_id, sender, subject, draft_body, tier, created_at, "
        "ai_reasoning, suggested_actions "
        "FROM pending_approvals "
        "WHERE status = 'pending' "
        "ORDER BY tier, created_at DESC"
    )
    args: list[object] = []
    if limit is not None:
        query += " LIMIT ?"
        args.append(limit)

    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()

    now = datetime.utcnow()
    items: list[dict] = []
    for row in rows:
        try:
            created = datetime.strptime(row["created_at"][:19], "%Y-%m-%d %H:%M:%S")
            age_hours = round((now - created).total_seconds() / 3600, 1)
        except Exception:
            age_hours = 0.0

        draft_body = row["draft_body"] or ""
        items.append(
            {
                "ref_id": row["ref_id"],
                "sender": row["sender"] or "",
                "subject": row["subject"] or "",
                "tier": int(row["tier"]) if row["tier"] else 3,
                "tier_label": _TIER_LABELS.get(str(row["tier"]), "MEDIUM"),
                "preview": draft_body[:120],
                "draft_body": draft_body,
                "body": draft_body,
                "age_hours": age_hours,
                "ai_reasoning": row["ai_reasoning"] or "",
                "suggested_actions": row["suggested_actions"] or "",
            }
        )
    return items


def find_pending_email(search: str) -> dict:
    """Best-effort match against ref_id, sender, or subject."""
    if not search:
        return {}

    needle = search.strip().lower()
    if not needle:
        return {}

    for item in list_pending_email_items():
        haystack = " ".join(
            [
                str(item.get("ref_id", "")),
                str(item.get("sender", "")),
                str(item.get("subject", "")),
                str(item.get("preview", "")),
            ]
        ).lower()
        if needle in haystack:
            return item
    return {}


def get_pending_email_summary() -> dict:
    """Counts used by dashboard and status endpoints."""
    items = list_pending_email_items()
    urgent_count = sum(1 for item in items if int(item.get("tier", 5)) <= 1)
    return {
        "pending_count": len(items),
        "pending_emails": len(items),
        "urgent_count": urgent_count,
        "items": items,
    }
