"""
SOVEREIGN ENGINE — BYOK service layer.

Stores user API keys encrypted via Fernet (services/crypto.py).
DB table: byok_keys(user_id, provider, encrypted_key, extra, updated_at)

Usage in AI services:
    from services.byok import get_effective_key
    key = get_effective_key(user_id, "openrouter") or os.getenv("OPENROUTER_API_KEY")
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone

from services.crypto import encrypt_dict, decrypt_dict
from services.database import DB_PATH

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ["openrouter", "gemini", "elevenlabs"]


def _ensure_table():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS byok_keys (
            user_id   TEXT NOT NULL,
            provider  TEXT NOT NULL,
            enc_key   TEXT NOT NULL,
            extra     TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, provider)
        )
    """)
    conn.commit()
    conn.close()


_ensure_table()


def save_byok_key(user_id: str, provider: str, api_key: str, extra: str = None):
    enc = encrypt_dict({"key": api_key, "extra": extra or ""})
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute(
        "INSERT OR REPLACE INTO byok_keys (user_id, provider, enc_key, extra, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, provider, enc, extra or "", datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
    logger.info(f"BYOK: saved {provider} key for user {user_id[:8]}...")


def get_byok_status(user_id: str) -> dict:
    """Return {provider: {configured: bool, updated_at: str}} — never expose key."""
    _ensure_table()
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT provider, updated_at FROM byok_keys WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    configured = {r["provider"]: {"configured": True, "updated_at": r["updated_at"]} for r in rows}
    # Fill in unconfigured providers
    for p in SUPPORTED_PROVIDERS:
        if p not in configured:
            configured[p] = {"configured": False, "updated_at": None}
    return configured


def get_effective_key(user_id: str, provider: str) -> str:
    """Return decrypted user key if set, else empty string (caller falls back to env)."""
    if not user_id:
        return ""
    _ensure_table()
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20)
        row = conn.execute(
            "SELECT enc_key FROM byok_keys WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        ).fetchone()
        conn.close()
        if row:
            data = decrypt_dict(row[0])
            return data.get("key", "")
    except Exception as e:
        logger.warning(f"BYOK get_effective_key error for {provider}: {e}")
    return ""


def delete_byok_key(user_id: str, provider: str):
    _ensure_table()
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute(
        "DELETE FROM byok_keys WHERE user_id = ? AND provider = ?", (user_id, provider)
    )
    conn.commit()
    conn.close()
    logger.info(f"BYOK: deleted {provider} key for user {user_id[:8]}...")
