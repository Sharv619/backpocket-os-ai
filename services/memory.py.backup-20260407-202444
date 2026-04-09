"""
BackPocket Memory System
=======================
Simple persistent memory using SQLite - no external server needed!
"""

import sqlite3
import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"

def init_memory():
    """Initialize memory tables."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            source TEXT DEFAULT 'twin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON chat_messages(conversation_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_time ON chat_messages(timestamp)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_conv_source ON chat_conversations(source)
    ''')
    
    # Document memory (what we learned from each document)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            entity_name TEXT,
            abn TEXT,
            phone TEXT,
            email TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_message(session_id: str, role: str, content: str):
    """Add a message to conversation memory."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversation_memory (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()


def save_message_instant(conversation_id: str, role: str, content: str) -> str:
    """Save a message INSTANTLY to database - like ChatGPT/Claude chat history.
    
    Returns the message_id for reference.
    """
    msg_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO chat_messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
        (msg_id, conversation_id, role, content)
    )
    
    cursor.execute(
        "UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    
    conn.commit()
    conn.close()
    return msg_id


def create_conversation(title: str = None, source: str = "twin") -> str:
    """Create a new conversation thread.
    
    Args:
        title: Display name for the conversation
        source: Which AI assistant - 'twin', 'opencode', 'claude', etc.
    """
    conv_id = str(uuid.uuid4())
    if not title:
        if source == "opencode":
            title = f"OpenCode {datetime.now().strftime('%b %d, %H:%M')}"
        else:
            title = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"
    
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_conversations (id, title, source) VALUES (?, ?, ?)",
        (conv_id, title, source)
    )
    conn.commit()
    conn.close()
    return conv_id


def save_opencode_message(conversation_id: str, role: str, content: str) -> str:
    """Save an OpenCode chat message instantly to database."""
    return save_message_instant(conversation_id, role, content)


def create_opencode_conversation(title: str = None) -> str:
    """Create a new OpenCode conversation thread."""
    return create_conversation(title, source="opencode")


def get_opencode_conversations(limit: int = 30) -> List[Dict]:
    """Get all OpenCode conversations for history sidebar."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, updated_at 
        FROM chat_conversations 
        WHERE source = 'opencode'
        ORDER BY updated_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_twin_conversations(limit: int = 30) -> List[Dict]:
    """Get all Twin conversations for history sidebar."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, updated_at 
        FROM chat_conversations 
        WHERE source = 'twin'
        ORDER BY updated_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_conversation_messages(conversation_id: str, limit: int = 50) -> List[Dict]:
    """Get all messages in a conversation."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, role, content, timestamp 
        FROM chat_messages 
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
        LIMIT ?
    """, (conversation_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_conversations(limit: int = 20, source: str = None) -> List[Dict]:
    """Get list of all conversations (for sidebar/history).
    
    Args:
        limit: Max number of conversations to return
        source: Filter by source ('twin', 'opencode', etc.) or None for all
    """
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if source:
        cursor.execute("""
            SELECT id, title, source, updated_at 
            FROM chat_conversations 
            WHERE source = ?
            ORDER BY updated_at DESC
            LIMIT ?
        """, (source, limit))
    else:
        cursor.execute("""
            SELECT id, title, source, updated_at 
            FROM chat_conversations 
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_messages(limit: int = 20) -> List[Dict]:
    """Get the most recent messages across all conversations."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.conversation_id, m.role, m.content, m.timestamp, c.title
        FROM chat_messages m
        JOIN chat_conversations c ON m.conversation_id = c.id
        ORDER BY m.timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_conversation(session_id: str, limit: int = 10) -> List[Dict]:
    """Get recent conversation history."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, timestamp 
        FROM conversation_memory 
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def remember_document(file_path: str, entity_name: str = None, abn: str = None, 
                      phone: str = None, email: str = None, notes: str = None):
    """Store what we learned from a document."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO document_memory (file_path, entity_name, abn, phone, email, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (file_path, entity_name, abn, phone, email, notes))
    conn.commit()
    conn.close()

def find_similar_document(entity_name: str = None, abn: str = None, 
                          phone: str = None, email: str = None) -> Optional[Dict]:
    """Find a similar document we've processed before."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Build query based on what we have
    conditions = []
    params = []
    
    if entity_name:
        conditions.append("entity_name LIKE ?")
        params.append(f"%{entity_name}%")
    if abn:
        conditions.append("abn = ?")
        params.append(abn)
    if phone:
        conditions.append("phone = ?")
        params.append(phone)
    if email:
        conditions.append("email = ?")
        params.append(email)
    
    if not conditions:
        conn.close()
        return None
    
    query = f"SELECT * FROM document_memory WHERE {' OR '.join(conditions)} ORDER BY created_at DESC LIMIT 1"
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def set_preference(key: str, value: str):
    """Store a user preference."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_memory (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (key, value))
    conn.commit()
    conn.close()

def get_preference(key: str) -> Optional[str]:
    """Get a user preference."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM user_memory WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_memory_context() -> str:
    """Get all relevant memory context for Twin to use."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    context_parts = []
    
    # Get recent conversations
    cursor.execute("""
        SELECT role, content FROM conversation_memory 
        ORDER BY timestamp DESC LIMIT 5
    """)
    recent = cursor.fetchall()
    if recent:
        context_parts.append("RECENT CONVERSATIONS:")
        for msg in reversed(recent):
            context_parts.append(f"  {msg['role']}: {msg['content'][:100]}...")
    
    # Get recent documents
    cursor.execute("""
        SELECT entity_name, abn, notes FROM document_memory 
        ORDER BY created_at DESC LIMIT 5
    """)
    docs = cursor.fetchall()
    if docs:
        context_parts.append("\nRECENT DOCUMENTS:")
        for doc in docs:
            if doc['entity_name']:
                context_parts.append(f"  - {doc['entity_name']} (ABN: {doc['abn'] or 'N/A'})")
    
    # Get user preferences
    cursor.execute("SELECT key, value FROM user_memory")
    prefs = cursor.fetchall()
    if prefs:
        context_parts.append("\nPREFERENCES:")
        for pref in prefs:
            context_parts.append(f"  {pref['key']}: {pref['value']}")
    
    conn.close()
    return "\n".join(context_parts) if context_parts else "No memory yet."


def search_messages(query: str, source: str = None, limit: int = 20) -> List[Dict]:
    """Search all messages across conversations.
    
    Args:
        query: Search term to find in message content
        source: Filter by source ('twin', 'opencode') or None for all
        limit: Max results to return
    """
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if source:
        cursor.execute("""
            SELECT m.id, m.conversation_id, m.role, m.content, m.timestamp, c.title, c.source
            FROM chat_messages m
            JOIN chat_conversations c ON m.conversation_id = c.id
            WHERE m.content LIKE ? AND c.source = ?
            ORDER BY m.timestamp DESC
            LIMIT ?
        """, (f"%{query}%", source, limit))
    else:
        cursor.execute("""
            SELECT m.id, m.conversation_id, m.role, m.content, m.timestamp, c.title, c.source
            FROM chat_messages m
            JOIN chat_conversations c ON m.conversation_id = c.id
            WHERE m.content LIKE ?
            ORDER BY m.timestamp DESC
            LIMIT ?
        """, (f"%{query}%", limit))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_latest_opencode_conversation() -> Optional[Dict]:
    """Get the most recent OpenCode conversation."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, updated_at 
        FROM chat_conversations 
        WHERE source = 'opencode'
        ORDER BY updated_at DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_conversation_title(conversation_id: str, title: str):
    """Update a conversation's title."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE chat_conversations SET title = ? WHERE id = ?",
        (title, conversation_id)
    )
    conn.commit()
    conn.close()


def get_message_count(conversation_id: str) -> int:
    """Get number of messages in a conversation."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM chat_messages WHERE conversation_id = ?",
        (conversation_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count


def generate_conversation_title(conversation_id: str) -> Optional[str]:
    """Generate a smart title from conversation content using AI.
    
    Returns None if no AI available or generation fails.
    """
    try:
        from services.gemini import get_gemini_client
        
        messages = get_conversation_messages(conversation_id, limit=10)
        if len(messages) < 2:
            return None
        
        combined = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        client = get_gemini_client()
        if not client:
            return None
        
        prompt = f"""Based on this conversation, generate a SHORT title (max 50 characters).

Rules:
- Start with relevant topic (e.g., "Email draft:", "Bug fix:", "Client:")
- Be specific but brief
- Use the user's language (English)
- No quotes, no special characters

Conversation:
{combined[:500]}

Title:"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        if response and response.text:
            title = response.text.strip()[:50]
            update_conversation_title(conversation_id, title)
            return title
        
        return None
    except Exception:
        return None


def auto_title_if_needed(conversation_id: str, min_messages: int = 3) -> Optional[str]:
    """Auto-generate title if conversation has enough messages and no custom title.
    
    Only generates if title is still the default "Chat Apr 03, 11:20" format.
    """
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM chat_conversations WHERE id = ?", (conversation_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    current_title = row[0]
    
    if current_title and not current_title.startswith(("Chat ", "OpenCode ")):
        return None
    
    count = get_message_count(conversation_id)
    if count >= min_messages:
        return generate_conversation_title(conversation_id)
    
    return None


# ============ SOPs (Standard Operating Procedures) ============

def init_sops():
    """Initialize SOPs table with default procedures."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title TEXT,
            steps TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM sops")
    if cursor.fetchone()[0] == 0:
        default_sops = [
            {
                "category": "system",
                "title": "Restart Server",
                "steps": json.dumps([
                    "1. Press Ctrl+C in terminal running main.py",
                    "2. Wait for 'Keyboard interrupt' message",
                    "3. Run: python main.py",
                    "4. Wait for 'BACKPOCKET TWIN VERSION 2.2 STARTED'",
                    "5. Refresh dashboard browser tab"
                ]),
                "description": "How to restart BackPocket server after changes or crash"
            },
            {
                "category": "system",
                "title": "Check Server Status",
                "steps": json.dumps([
                    "1. Open browser to http://localhost:8000",
                    "2. Check dashboard shows 'Server: Running'",
                    "3. Look for green status indicators",
                    "4. Try sending a test message to Twin",
                    "5. Check terminal for any error messages"
                ]),
                "description": "Verify BackPocket is running correctly"
            },
            {
                "category": "system",
                "title": "Backup Database",
                "steps": json.dumps([
                    "1. Stop the server (Ctrl+C)",
                    "2. Copy backpocket.db to backup folder",
                    "3. Name backup: backpocket_YYYYMMDD.db",
                    "4. Restart server",
                    "5. Verify backup file exists"
                ]),
                "description": "Create a backup of all data before major changes"
            },
            {
                "category": "chat",
                "title": "Start New Chat Topic",
                "steps": json.dumps([
                    "1. Click 'New Chat' or 'New Conversation' button",
                    "2. System creates new conversation thread",
                    "3. AI auto-generates title after 3 messages",
                    "4. You can rename title anytime",
                    "5. Chat is saved automatically"
                ]),
                "description": "Begin a fresh conversation thread"
            },
            {
                "category": "chat",
                "title": "Search Past Chats",
                "steps": json.dumps([
                    "1. Click 'History' or 'Conversations' in sidebar",
                    "2. See all saved conversations",
                    "3. Filter by Twin or OpenCode",
                    "4. Click any conversation to view",
                    "5. Use search bar for keyword search"
                ]),
                "description": "Find and revisit previous conversations"
            },
            {
                "category": "chat",
                "title": "Edit Chat Title",
                "steps": json.dumps([
                    "1. Hover over conversation in sidebar",
                    "2. Click edit/pencil icon",
                    "3. Type new name",
                    "4. Press Enter or click Save",
                    "5. Title updates instantly"
                ]),
                "description": "Rename a conversation for better organization"
            },
            {
                "category": "email",
                "title": "Review Pending Approvals",
                "steps": json.dumps([
                    "1. Open dashboard",
                    "2. Click 'Pending' tab or section",
                    "3. See list of emails awaiting approval",
                    "4. Click any item to view details",
                    "5. Choose: Approve / Revise / Delete"
                ]),
                "description": "Review emails that need your decision"
            },
            {
                "category": "email",
                "title": "Draft Email Response",
                "steps": json.dumps([
                    "1. Select email from pending list",
                    "2. Click 'Draft Response'",
                    "3. AI generates draft based on context",
                    "4. Edit draft if needed",
                    "5. Click 'Send' when ready"
                ]),
                "description": "Create and send email reply using AI"
            },
            {
                "category": "instructions",
                "title": "Add New Instruction",
                "steps": json.dumps([
                    "1. Go to Instructions section in dashboard",
                    "2. Click 'Add Instruction'",
                    "3. Enter sender email or pattern",
                    "4. Write the instruction text",
                    "5. Save - Twin will follow it automatically"
                ]),
                "description": "Teach Twin how to handle specific senders"
            },
            {
                "category": "instructions",
                "title": "Update Existing Instruction",
                "steps": json.dumps([
                    "1. Find instruction in list",
                    "2. Click to edit",
                    "3. Change text or sender",
                    "4. Save changes",
                    "5. Twin applies update immediately"
                ]),
                "description": "Modify an instruction you've already created"
            },
            {
                "category": "debug",
                "title": "View Error Logs",
                "steps": json.dumps([
                    "1. Open terminal running main.py",
                    "2. Scroll up to see recent errors",
                    "3. Errors show in red or with ERROR label",
                    "4. Note timestamp and error message",
                    "5. Check docs/ERROR_LOG.md for known fixes"
                ]),
                "description": "Find and understand error messages"
            },
            {
                "category": "debug",
                "title": "Clear Chat Cache",
                "steps": json.dumps([
                    "1. Close all browser tabs to dashboard",
                    "2. Clear browser cache (Ctrl+Shift+Del)",
                    "3. Restart browser",
                    "4. Refresh dashboard",
                    "5. Chat history loads from database"
                ]),
                "description": "Fix display issues by clearing local cache"
            }
        ]
        
        for sop in default_sops:
            cursor.execute(
                "INSERT INTO sops (category, title, steps, description) VALUES (?, ?, ?, ?)",
                (sop["category"], sop["title"], sop["steps"], sop["description"])
            )
        conn.commit()
        logger.info(f"Initialized {len(default_sops)} default SOPs")
    
    conn.close()


def get_sops(category: str = None) -> List[Dict]:
    """Get SOPs, optionally filtered by category."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if category:
        cursor.execute(
            "SELECT * FROM sops WHERE category = ? ORDER BY title",
            (category,)
        )
    else:
        cursor.execute("SELECT * FROM sops ORDER BY category, title")
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_sop_categories() -> List[str]:
    """Get list of all SOP categories."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM sops ORDER BY category")
    categories = [r[0] for r in cursor.fetchall()]
    conn.close()
    return categories


def add_sop(category: str, title: str, steps: List[str], description: str = "") -> int:
    """Add a new SOP."""
    import json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sops (category, title, steps, description) VALUES (?, ?, ?, ?)",
        (category, title, json.dumps(steps), description)
    )
    conn.commit()
    sop_id = cursor.lastrowid
    conn.close()
    return sop_id


def search_sops(query: str) -> List[Dict]:
    """Search SOPs by keyword."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sops WHERE title LIKE ? OR description LIKE ? OR steps LIKE ?",
        (f"%{query}%", f"%{query}%", f"%{query}%")
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Auto-init with schema migration
def migrate_schema():
    """Add source column to existing chat_conversations if missing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(chat_conversations)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'source' not in columns:
        cursor.execute("ALTER TABLE chat_conversations ADD COLUMN source TEXT DEFAULT 'twin'")
        conn.commit()
    
    conn.close()

migrate_schema()
init_memory()
init_sops()
