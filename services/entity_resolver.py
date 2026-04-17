"""
BackPocket OS — Entity Resolver
Fuzzy matching of voice references ("the Penrith one", "that bloke") against live DB data.
"""

import sqlite3
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"


def _connect():
    return sqlite3.connect(DB_PATH, timeout=10)


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def resolve_entity(
    entity_type: str,
    fuzzy_ref: str,
    session_last_entity: dict | None = None,
) -> dict:
    """
    Resolve a fuzzy reference to a concrete entity.

    Returns: {
        "match": "exact" | "fuzzy" | "multiple" | "none",
        "entity": {...} or None,
        "candidates": [...] if multiple,
    }
    """
    if fuzzy_ref and fuzzy_ref.lower() in ("that", "that one", "the last one", "it", "this"):
        if session_last_entity and session_last_entity.get("type") == entity_type:
            return {"match": "exact", "entity": session_last_entity, "candidates": []}

    resolvers = {
        "lead": _resolve_lead,
        "quote": _resolve_quote,
        "payment": _resolve_payment,
        "email": _resolve_email,
    }

    resolver = resolvers.get(entity_type)
    if not resolver:
        return {"match": "none", "entity": None, "candidates": []}

    return resolver(fuzzy_ref)


def resolve_lead_by_id(lead_id: int) -> dict | None:
    try:
        conn = _connect()
        cur = conn.execute("SELECT id, client_name, job_type, location, urgency, estimated_budget, status FROM leads WHERE id = ?", (lead_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "type": "lead", "id": row[0], "client_name": row[1],
                "job_type": row[2], "location": row[3], "urgency": row[4],
                "estimated_budget": row[5], "status": row[6],
            }
    except Exception as e:
        logger.error(f"Lead lookup error: {e}")
    return None


def resolve_quote_by_id(quote_id: int) -> dict | None:
    try:
        conn = _connect()
        cur = conn.execute(
            "SELECT id, lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total_amount, status FROM quotes WHERE id = ?",
            (quote_id,),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "type": "quote", "id": row[0], "lead_id": row[1],
                "client_name": row[2], "job_type": row[3],
                "materials_cost": row[4], "labor_cost": row[5],
                "markup_percent": row[6], "total_amount": row[7], "status": row[8],
            }
    except Exception as e:
        logger.error(f"Quote lookup error: {e}")
    return None


def _resolve_lead(fuzzy_ref: str) -> dict:
    try:
        ref_int = int(fuzzy_ref)
        entity = resolve_lead_by_id(ref_int)
        if entity:
            return {"match": "exact", "entity": entity, "candidates": []}
    except (ValueError, TypeError):
        pass

    try:
        conn = _connect()
        cur = conn.execute("SELECT id, client_name, job_type, location, urgency, estimated_budget, status FROM leads ORDER BY id DESC LIMIT 50")
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Lead search error: {e}")
        return {"match": "none", "entity": None, "candidates": []}

    return _fuzzy_match_rows(
        rows, fuzzy_ref, "lead",
        fields=["client_name", "job_type", "location"],
        col_names=["id", "client_name", "job_type", "location", "urgency", "estimated_budget", "status"],
    )


def _resolve_quote(fuzzy_ref: str) -> dict:
    try:
        ref_int = int(fuzzy_ref)
        entity = resolve_quote_by_id(ref_int)
        if entity:
            return {"match": "exact", "entity": entity, "candidates": []}
    except (ValueError, TypeError):
        pass

    try:
        conn = _connect()
        cur = conn.execute(
            "SELECT id, lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total_amount, status FROM quotes ORDER BY id DESC LIMIT 50"
        )
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Quote search error: {e}")
        return {"match": "none", "entity": None, "candidates": []}

    return _fuzzy_match_rows(
        rows, fuzzy_ref, "quote",
        fields=["client_name", "job_type"],
        col_names=["id", "lead_id", "client_name", "job_type", "materials_cost", "labor_cost", "markup_percent", "total_amount", "status"],
    )


def _resolve_payment(fuzzy_ref: str) -> dict:
    try:
        conn = _connect()
        cur = conn.execute("SELECT id, quote_id, client_name, amount, status FROM payments ORDER BY id DESC LIMIT 50")
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Payment search error: {e}")
        return {"match": "none", "entity": None, "candidates": []}

    return _fuzzy_match_rows(
        rows, fuzzy_ref, "payment",
        fields=["client_name"],
        col_names=["id", "quote_id", "client_name", "amount", "status"],
    )


def _resolve_email(fuzzy_ref: str) -> dict:
    try:
        conn = _connect()
        cur = conn.execute("SELECT id, sender, subject FROM email_interactions ORDER BY id DESC LIMIT 50")
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Email search error: {e}")
        return {"match": "none", "entity": None, "candidates": []}

    return _fuzzy_match_rows(
        rows, fuzzy_ref, "email",
        fields=["sender", "subject"],
        col_names=["id", "sender", "subject"],
    )


def _fuzzy_match_rows(
    rows: list,
    fuzzy_ref: str,
    entity_type: str,
    fields: list[str],
    col_names: list[str],
    threshold: float = 0.4,
) -> dict:
    if not rows:
        return {"match": "none", "entity": None, "candidates": []}

    scored = []
    ref_lower = fuzzy_ref.lower()

    for row in rows:
        row_dict = {col_names[i]: row[i] for i in range(len(col_names))}
        row_dict["type"] = entity_type

        best_score = 0.0
        for field in fields:
            field_idx = col_names.index(field) if field in col_names else -1
            if field_idx < 0 or field_idx >= len(row):
                continue
            val = str(row[field_idx] or "")
            if ref_lower in val.lower():
                best_score = max(best_score, 0.85)
            else:
                best_score = max(best_score, _similarity(ref_lower, val))

        if best_score >= threshold:
            scored.append((best_score, row_dict))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return {"match": "none", "entity": None, "candidates": []}

    if len(scored) == 1 or (scored[0][0] - scored[1][0] > 0.2 if len(scored) > 1 else True):
        return {"match": "fuzzy", "entity": scored[0][1], "candidates": []}

    top_candidates = [s[1] for s in scored[:5]]
    return {"match": "multiple", "entity": None, "candidates": top_candidates}


def get_available_entities(screen_context: str) -> dict:
    """Get summary of available entities for the current screen context (for LLM context)."""
    entities = {}

    try:
        conn = _connect()

        if screen_context in ("construction", "dashboard"):
            cur = conn.execute("SELECT id, client_name, location, status FROM leads ORDER BY id DESC LIMIT 10")
            entities["recent_leads"] = [
                {"id": r[0], "name": r[1], "location": r[2], "status": r[3]} for r in cur.fetchall()
            ]
            cur = conn.execute("SELECT id, client_name, job_type, total_amount, status FROM quotes ORDER BY id DESC LIMIT 10")
            entities["recent_quotes"] = [
                {"id": r[0], "name": r[1], "job_type": r[2], "total": r[3], "status": r[4]} for r in cur.fetchall()
            ]

        if screen_context in ("inbox", "dashboard"):
            cur = conn.execute("SELECT id, sender, subject FROM email_interactions ORDER BY id DESC LIMIT 10")
            entities["recent_emails"] = [
                {"id": r[0], "sender": r[1], "subject": r[2]} for r in cur.fetchall()
            ]

        conn.close()
    except Exception as e:
        logger.error(f"Entity context error: {e}")

    return entities
