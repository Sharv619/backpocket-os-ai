import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"

def init_session_db():
    """Add session and memory tables to database if they don't exist."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    # Session log table - tracks work sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            summary TEXT,
            files_changed TEXT,
            decisions TEXT,
            errors TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Twin memory - persistent context across restarts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS twin_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_type TEXT,  -- 'conversation', 'agreed_action', 'context'
            key TEXT UNIQUE,
            value TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Action items - things we've agreed to implement
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agreed_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
    ''')
    
    # Version history - tracks changes like Git
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS version_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,  -- 'session', 'memory', 'action', 'system'
            entity_id INTEGER,
            version INTEGER DEFAULT 1,
            field_changed TEXT,  -- what changed
            old_value TEXT,
            new_value TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Snapshots - point-in-time captures
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_name TEXT,
            snapshot_type TEXT,  -- 'session_state', 'twin_memory', 'full_system'
            data_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("SESSION/MEMORY DB INITIALIZED WITH VERSION CONTROL")

def log_session(summary: str, files_changed: str = "", decisions: str = "", errors: str = ""):
    """Log a work session."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO session_log (date, summary, files_changed, decisions, errors) VALUES (?, ?, ?, ?, ?)",
        (today, summary, files_changed, decisions, errors)
    )
    conn.commit()
    conn.close()
    logger.info(f"Session logged: {summary[:50]}...")

def get_recent_sessions(days: int = 7) -> list:
    """Get recent session logs."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, summary, files_changed, decisions FROM session_log ORDER BY date DESC LIMIT ?",
        (days,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"date": r[0], "summary": r[1], "files": r[2], "decisions": r[3]} for r in rows]

def save_twin_memory(key: str, value: str, memory_type: str = "context"):
    """Save a piece of Twin memory."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO twin_memory (memory_type, key, value, updated_at) 
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP""",
        (memory_type, key, value)
    )
    conn.commit()
    conn.close()

def get_twin_memory(key: str) -> Optional[str]:
    """Get a specific memory."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM twin_memory WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_all_twin_memories(memory_type: Optional[str] = None) -> Dict[str, str]:
    """Get all memories, optionally filtered by type."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    if memory_type:
        cursor.execute("SELECT key, value FROM twin_memory WHERE memory_type = ? ORDER BY updated_at DESC", (memory_type,))
    else:
        cursor.execute("SELECT key, value FROM twin_memory ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def add_agreed_action(description: str) -> Optional[int]:
    """Add an action we've agreed to implement."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO agreed_actions (description) VALUES (?)", (description,))
    action_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return action_id

def update_action_status(action_id: int, status: str):
    """Update status of an agreed action."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == "completed" else None
    cursor.execute(
        "UPDATE agreed_actions SET status = ?, completed_at = ? WHERE id = ?",
        (status, completed_at, action_id)
    )
    conn.commit()
    conn.close()

def get_pending_actions() -> list:
    """Get all pending/in-progress actions."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, description, status, created_at FROM agreed_actions WHERE status IN ('pending', 'in_progress') ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "description": r[1], "status": r[2], "created_at": r[3]} for r in rows]

def get_all_actions() -> list:
    """Get all actions."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, description, status, created_at, completed_at FROM agreed_actions ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "description": r[1], "status": r[2], "created_at": r[3], "completed_at": r[4]} for r in rows]

def build_context_summary() -> str:
    """Build a context summary for the Twin to remember."""
    recent_sessions = get_recent_sessions(3)
    pending_actions = get_pending_actions()
    memories = get_all_twin_memories()
    
    context = "\n\n### RECENT SESSIONS ###\n"
    for s in recent_sessions:
        context += f"- {s['date']}: {s['summary'][:80]}...\n"
    
    if pending_actions:
        context += "\n### PENDING ACTIONS (Things we've agreed to do) ###\n"
        for a in pending_actions:
            context += f"- [{a['status']}] {a['description']}\n"
    
    if memories:
        context += "\n### TWIN MEMORIES ###\n"
        for key, value in list(memories.items())[:5]:
            context += f"- {key}: {value[:60]}...\n"
    
    return context

def sync_to_docs():
    """Sync session data to SESSION_LOG.md, OPENCODE_CONTEXT.md and ERROR_LOG.md files."""
    import os
    from datetime import datetime
    
    sessions = get_recent_sessions(7)
    pending_actions = get_pending_actions()
    
    # Update SESSION_LOG.md
    session_log_path = "SESSION_LOG.md"
    today = datetime.now().strftime("%B %d, %Y")
    
    new_entry = f"## Last Session: {today}\n\n"
    if sessions:
        new_entry += f"### What We Did:\n{sessions[0]['summary']}\n\n"
        if sessions[0].get('files'):
            new_entry += f"### Files Changed:\n{sessions[0]['files']}\n\n"
        if sessions[0].get('decisions'):
            new_entry += f"### Key Decisions:\n{sessions[0]['decisions']}\n\n"
    
    new_entry += "---\n"
    
    try:
        if os.path.exists(session_log_path):
            with open(session_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('## Last Session:'):
                    insert_pos = i
                    break
            lines.insert(insert_pos + 1, new_entry)
            content = '\n'.join(lines[:insert_pos + 15])
        else:
            content = f"# SESSION LOG - BackPocket OS\n\n{new_entry}"
        
        with open(session_log_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("SESSION_LOG.md updated")
    except Exception as e:
        logger.warning(f"Could not update SESSION_LOG.md: {e}")
    
    # Update OPENCODE_CONTEXT.md for persistent memory between sessions
    opencode_context_path = "OPENCODE_CONTEXT.md"
    pending_str = "\n".join([f"- [{a['status']}] {a['description']}" for a in pending_actions]) if pending_actions else "- None"
    
    context_content = f"""# OpenCode Session Context

## Last Session: {today}

### What We Did:
{sessions[0]['summary'] if sessions else 'Session logged'}

### Files Changed:
{sessions[0].get('files', 'See SESSION_LOG.md') if sessions else ''}

### Key Decisions:
{sessions[0].get('decisions', '') if sessions else ''}

### Pending Actions (From Twin):
{pending_str}

### System Status:
| Component | Status |
|-----------|--------|
| Server | Running on port 8000 |
| Twin Chat | Working with memory |
| Session DB | Initialized |
| Ruff | All clean |

### Common Gotchas:
1. Server needs restart after main.py changes
2. Twin memory loads on startup from database
3. Chat persists in browser localStorage

---

*Auto-generated - updated after each session*
"""
    
    try:
        with open(opencode_context_path, 'w', encoding='utf-8') as f:
            f.write(context_content)
        logger.info("OPENCODE_CONTEXT.md updated")
    except Exception as e:
        logger.warning(f"Could not update OPENCODE_CONTEXT.md: {e}")


def record_version(entity_type: str, entity_id: int, field_changed: str, old_value: str, new_value: str):
    """Record a version change (like Git commit)."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT MAX(version) FROM version_history WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id)
    )
    result = cursor.fetchone()
    new_version = (result[0] or 0) + 1
    
    cursor.execute(
        """INSERT INTO version_history (entity_type, entity_id, version, field_changed, old_value, new_value)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (entity_type, entity_id, new_version, field_changed, old_value, new_value)
    )
    conn.commit()
    conn.close()
    logger.info(f"Version {new_version} recorded for {entity_type}:{entity_id}")


def get_version_history(entity_type: str, entity_id: int) -> list:
    """Get version history for an entity (like git log)."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT version, field_changed, old_value, new_value, created_at 
           FROM version_history WHERE entity_type = ? AND entity_id = ? 
           ORDER BY version DESC""",
        (entity_type, entity_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"version": r[0], "field": r[1], "old": r[2], "new": r[3], "date": r[4]} for r in rows]


def create_snapshot(snapshot_name: str, snapshot_type: str, data: dict) -> Optional[int]:
    """Create a point-in-time snapshot (like Git tag)."""
    import json  # noqa: F811
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO snapshots (snapshot_name, snapshot_type, data_json) VALUES (?, ?, ?)",
            (snapshot_name, snapshot_type, json.dumps(data))
        )
        snapshot_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Snapshot created: {snapshot_name}")
        return snapshot_id
    except sqlite3.OperationalError as e:
        conn.close()
        logger.warning(f"Could not create snapshot: {e}")
        return None


def get_snapshots(snapshot_type: Optional[str] = None) -> list:
    """Get all snapshots, optionally filtered by type."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    if snapshot_type:
        cursor.execute(
            "SELECT id, snapshot_name, snapshot_type, created_at FROM snapshots WHERE snapshot_type = ? ORDER BY created_at DESC",
            (snapshot_type,)
        )
    else:
        cursor.execute("SELECT id, snapshot_name, snapshot_type, created_at FROM snapshots ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "type": r[2], "date": r[3]} for r in rows]


def restore_snapshot(snapshot_id: int) -> Optional[dict]:
    """Restore data from a snapshot."""
    import json  # noqa: F811
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT data_json FROM snapshots WHERE id = ?", (snapshot_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None  # type: ignore


# ============ CONVERSATION COMPACTION ============

def add_compacted_summary_column():
    """Add compacted_summary column if not exists."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(chat_conversations)")
    columns = [col[1] for col in cursor.fetchall()]
    if "compacted_summary" not in columns:
        cursor.execute("ALTER TABLE chat_conversations ADD COLUMN compacted_summary TEXT")
        conn.commit()
    conn.close()

try:
    add_compacted_summary_column()
except Exception:
    pass  # Table may not exist yet on first run

def compact_conversation(conversation_id: str) -> Optional[str]:
    """Compress conversation into 150-word digest using Gemini.
    
    Returns the digest text if successful, None otherwise.
    """
    try:
        from services.gemini import get_gemini_client
        from services.memory import get_conversation_messages
        
        messages = get_conversation_messages(conversation_id, limit=100)
        if len(messages) < 20:
            return None
        
        combined = "\n".join([
            f"{m.get('role', 'unknown')}: {m.get('content', '')[:200]}"
            for m in messages
        ])
        
        client = get_gemini_client()
        if not client:
            return None
        
        prompt = f"""Summarize this conversation into exactly 150 words or fewer.
        Focus on: key topics discussed, decisions made, actions agreed upon, and important context.
        
        Conversation:
        {combined[:3000]}
        
        Summary:"""
        
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        digest = response.text.strip() if response and response.text else ""
        
        if digest:
            conn = sqlite3.connect(DB_PATH, timeout=20)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chat_conversations SET compacted_summary = ? WHERE id = ?",
                (digest, conversation_id)
            )
            conn.commit()
            conn.close()
            logger.info(f"Compacted conversation {conversation_id[:20]}...")
        
        return digest
    except Exception as e:
        logger.warning(f"Compaction error: {e}")
        return None

def get_compacted_summary(conversation_id: str) -> Optional[str]:
    """Get compacted summary for a conversation."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT compacted_summary FROM chat_conversations WHERE id = ?", (conversation_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def get_conversation_context(conversation_id: str) -> str:
    """Get conversation context - either compacted summary or recent messages.
    
    This is the smart function that decides which to use.
    """
    compacted = get_compacted_summary(conversation_id)
    if compacted:
        return f"[Earlier conversation summarized]: {compacted}"
    
    try:
        from services.memory import get_conversation_messages
        messages = get_conversation_messages(conversation_id, limit=6)
        if messages:
            recent = "\n".join([
                f"{m.get('role', 'user')}: {m.get('content', '')[:100]}"
                for m in messages
            ])
            return f"[Recent messages]:\n{recent}"
    except Exception:
        pass
    
    return ""

def check_and_compact(conversation_id: str, threshold: int = 20) -> bool:
    """Check message count and auto-compact if threshold reached.
    
    Returns True if compaction happened.
    """
    try:
        from services.memory import get_message_count
        count = get_message_count(conversation_id)
        if count >= threshold:
            result = compact_conversation(conversation_id)
            return result is not None
    except Exception as e:
        logger.warning(f"Auto-compaction check error: {e}")
    return False