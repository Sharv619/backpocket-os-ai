import sqlite3
import logging
from typing import Dict, List, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"

def _init_scheduler_db():
    """Ensure the social_posts table exists."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS social_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL, -- "facebook", "instagram", "linkedin"
            content TEXT NOT NULL,
            media_urls TEXT, -- JSON list of URLs
            scheduled_for DATETIME NOT NULL,
            status TEXT DEFAULT 'pending', -- pending, posted, failed
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def schedule_post(platform: str, content: str, scheduled_for: str, media_urls: List[str] = None) -> int:
    """
    Schedules a social media post.
    scheduled_for must be ISO format, e.g., 'YYYY-MM-DD HH:MM:SS'
    """
    _init_scheduler_db()
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    media_json = json.dumps(media_urls) if media_urls else "[]"
    
    cursor.execute('''
        INSERT INTO social_posts (platform, content, media_urls, scheduled_for)
        VALUES (?, ?, ?, ?)
    ''', (platform, content, media_json, scheduled_for))
    
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f"Scheduled new {platform} post for {scheduled_for} (ID: {post_id})")
    return post_id

def get_pending_posts() -> List[Dict[str, Any]]:
    """Retrieves all pending posts."""
    _init_scheduler_db()
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM social_posts WHERE status = 'pending' ORDER BY scheduled_for ASC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]

def mark_post_status(post_id: int, status: str):
    """Updates the status of a post (e.g., 'posted', 'failed')."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("UPDATE social_posts SET status = ? WHERE id = ?", (status, post_id))
    conn.commit()
    conn.close()
    logger.info(f"Marked post {post_id} as {status}")

def run_scheduler_tick():
    """
    Called by a background worker to post anything whose time has come.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pending = get_pending_posts()
    
    for post in pending:
        if post["scheduled_for"] <= now:
            logger.info(f"Posting to {post['platform']}... (ID: {post['id']})")
            # In a real system, we'd call the Facebook/Instagram Graph API here.
            # For now, just mark it as posted.
            mark_post_status(post["id"], "posted")
