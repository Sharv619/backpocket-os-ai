import sqlite3
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"

def init_db():
    """Build the memory if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrency and performance
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('PRAGMA synchronous=NORMAL;')
    
    # 1. Table for Email Deduplication (The "Seen" List)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_messages (
            message_id TEXT PRIMARY KEY,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Table for Pending Approvals (The "Waitlist")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_approvals (
            ref_id TEXT PRIMARY KEY,
            message_id TEXT,
            thread_id TEXT,
            sender TEXT,
            subject TEXT,
            draft_body TEXT,
            delivered_to TEXT,
            tier TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_nudge_at DATETIME
        )
    ''')
    
    conn.commit()

    # Migration: Add last_nudge_at to existing databases
    try:
        cursor.execute("ALTER TABLE pending_approvals ADD COLUMN last_nudge_at DATETIME")
        conn.commit()
    except sqlite3.OperationalError:
        pass # already exists
        
    # 3. Table for Corrections (Cherry's feedback on drafts) - with learning metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref_id TEXT,
            correction_type TEXT,  -- 'revise', 'approve', 'custom'
            sender TEXT,
            subject TEXT,
            subject_keywords TEXT,
            original_draft TEXT,
            corrected_draft TEXT,
            feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ref_id) REFERENCES pending_approvals(ref_id)
        )
    ''')
    
    # 4. Table for Action History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref_id TEXT,
            action TEXT,  -- 'approved', 'revised', 'archived', 'trashed'
            tier TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. Table for Sender Instructions (Twin learns specific instructions for senders)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sender_instructions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT UNIQUE,
            instructions TEXT,
            category TEXT,  -- 'client', 'supplier', 'builder', etc.
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 6. Instructions table (previously created on first write — moved here)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instruction_text TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            target TEXT DEFAULT '',
            target_type TEXT DEFAULT '',
            description TEXT DEFAULT '',
            is_critical INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            is_active INTEGER DEFAULT 1,
            is_test_mode INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Instruction revisions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instruction_revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instruction_id INTEGER,
            action TEXT,
            changes_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 8. Instruction categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instruction_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 9-13. Construction tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            job_type TEXT,
            location TEXT,
            pain_points TEXT,
            scope_items TEXT,
            urgency TEXT,
            estimated_budget DECIMAL(10,2),
            timeline TEXT,
            status TEXT DEFAULT 'new',
            extracted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            client_name TEXT,
            job_type TEXT,
            description TEXT,
            scope_items TEXT,
            materials_cost DECIMAL(10,2),
            labor_cost DECIMAL(10,2),
            markup_percent DECIMAL(5,2),
            total_amount DECIMAL(10,2),
            status TEXT DEFAULT 'draft',
            sent_date TIMESTAMP,
            accepted_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER,
            client_name TEXT,
            amount DECIMAL(10,2),
            status TEXT DEFAULT 'pending',
            due_date DATE,
            received_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(quote_id) REFERENCES quotes(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            file_type TEXT,
            category TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(quote_id) REFERENCES quotes(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER,
            visit_date DATE,
            transcript TEXT,
            materials_list TEXT,
            subcontractors_list TEXT,
            client_promises TEXT,
            action_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(quote_id) REFERENCES quotes(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_lead_id ON quotes(lead_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_quote_id ON payments(quote_id)")

    conn.commit()
    conn.close()
    logger.info("SQLITE MEMORY INITIALIZED")

def is_processed(message_id):
    """Check if we have already talked to this email."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute("SELECT 1 FROM processed_messages WHERE message_id = ?", (message_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_as_processed(message_id):
    """Remember that we have seen this email."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)", (message_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Error marking message as processed: {e}")
    finally:
        conn.close()

def save_pending_approval(ref_id, data):
    """Write a pending draft to the waitlist. Returns False if duplicate."""
    msg_id = data.get('message_id', '')
    sender = data.get('sender', '')
    subject = data.get('subject', '')
    
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    
    # Check for duplicates by message_id OR by sender+subject (same email sent twice)
    if msg_id:
        cursor.execute("SELECT ref_id FROM pending_approvals WHERE message_id = ?", (msg_id,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            logger.info(f"DUPLICATE SKIP: Message {msg_id} already pending as {existing[0]}")
            return False
    
    # Also check sender+subject combo to avoid same email creating multiple entries
    if sender and subject:
        cursor.execute("SELECT ref_id FROM pending_approvals WHERE sender = ? AND subject = ?", (sender, subject))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            logger.info(f"DUPLICATE SKIP: Same sender+subject already pending as {existing[0]}")
            return False
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO pending_approvals 
            (ref_id, message_id, thread_id, sender, subject, draft_body, delivered_to, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ref_id, 
            data['message_id'], 
            data['thread_id'], 
            data['sender'], 
            data['subject'], 
            data['draft_body'], 
            data['delivered_to'], 
            data['tier']
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error saving pending approval: {e}")
        conn.close()
        return False

def get_pending_approval(ref_id):
    """Retrieve a draft from the digital brain."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_approvals WHERE ref_id = ?", (ref_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_draft_body(ref_id, draft_body):
    """Update only the draft_body for an existing pending approval."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("UPDATE pending_approvals SET draft_body = ? WHERE ref_id = ?", (draft_body, ref_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def delete_pending_approval(ref_id):
    """Remove from waitlist after it is sent."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_approvals WHERE ref_id = ?", (ref_id,))
    conn.commit()
    conn.close()

def get_all_pending_refs():
    """Get a list of everything the Twin is waiting for."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT ref_id FROM pending_approvals")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_stale_approvals(hours=4):
    """Retrieve items that have been pending for longer than X hours and haven't been nudged recently."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # We nudge if it's > X hours old AND (never nudged OR last nudge was > X hours ago)
    interval = f"-{int(hours)} hours"
    cursor.execute("""
        SELECT * FROM pending_approvals
        WHERE status = 'pending'
        AND created_at <= datetime('now', ?)
        AND (last_nudge_at IS NULL OR last_nudge_at <= datetime('now', ?))
    """, (interval, interval))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_nudged(ref_id):
    """Updates the timestamp of the last nudge to prevent spam."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("UPDATE pending_approvals SET last_nudge_at = CURRENT_TIMESTAMP WHERE ref_id = ?", (ref_id,))
    conn.commit()
    conn.close()

def save_correction(ref_id, correction_type, original_draft, corrected_draft, feedback, sender="", subject=""):
    """Save Cherry's correction feedback with metadata for learning."""
    import re
    keywords = ""
    if subject:
        words = re.findall(r'\b\w{4,}\b', subject.lower())
        keywords = ",".join(words[:5])
    
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO corrections (ref_id, correction_type, sender, subject, subject_keywords, original_draft, corrected_draft, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ref_id, correction_type, sender, subject, keywords, original_draft, corrected_draft, feedback))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving correction: {e}")
    finally:
        conn.close()

def get_corrections(ref_id=None, limit=50):
    """Get all corrections, optionally filtered by ref_id."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if ref_id:
        cursor.execute("SELECT * FROM corrections WHERE ref_id = ? ORDER BY created_at DESC LIMIT ?", (ref_id, limit))
    else:
        cursor.execute("SELECT * FROM corrections ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_learned_patterns(sender_email="", subject="", limit=10):
    """Get learned correction patterns for similar emails."""
    import re
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    patterns = []
    
    # Try to match by sender
    if sender_email:
        cursor.execute("""
            SELECT * FROM corrections 
            WHERE sender LIKE ? AND correction_type = 'revise'
            ORDER BY created_at DESC LIMIT ?
        """, (f"%{sender_email}%", limit))
        patterns.extend(cursor.fetchall())
    
    # Try to match by subject keywords
    if subject:
        words = re.findall(r'\b\w{4,}\b', subject.lower())
        for word in words[:3]:
            cursor.execute("""
                SELECT * FROM corrections 
                WHERE subject_keywords LIKE ? AND correction_type = 'revise'
                ORDER BY created_at DESC LIMIT ?
            """, (f"%{word}%", limit // 2))
            patterns.extend(cursor.fetchall())
    
    conn.close()
    return [dict(p) for p in patterns[:limit]]

def log_action(ref_id, action, tier, notes=""):
    """Log an action to history."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO action_history (ref_id, action, tier, notes)
            VALUES (?, ?, ?, ?)
        ''', (ref_id, action, tier, notes))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Error logging action: {e}")
    finally:
        conn.close()

def get_action_history(limit=50):
    """Get recent action history."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM action_history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_draft(ref_id):
    """Get a draft by ref_id (same as get_pending_approval but returns draft_body specifically)."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT draft_body, sender, subject FROM pending_approvals WHERE ref_id = ?", (ref_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_sender_instruction(sender_email, instructions, category=""):
    """Save instructions for a specific sender (Twin will use these when drafting responses)."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO sender_instructions (sender_email, instructions, category, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (sender_email.lower(), instructions, category))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving sender instruction: {e}")
    finally:
        conn.close()

def get_sender_instruction(sender_email):
    """Get instructions for a specific sender."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sender_instructions WHERE sender_email = ?", (sender_email.lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_document_correction(file_path, user_correction, ai_response):
    """Save document corrections for learning."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO document_corrections (file_path, user_correction, ai_response, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (file_path, user_correction, ai_response))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving document correction: {e}")
    finally:
        conn.close()

def get_document_corrections(file_path=None):
    """Get document corrections, optionally filtered by file path."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if file_path:
        cursor.execute("SELECT * FROM document_corrections WHERE file_path = ? ORDER BY created_at DESC", (file_path,))
    else:
        cursor.execute("SELECT * FROM document_corrections ORDER BY created_at DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_sender_instructions():
    """Get all sender instructions."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sender_instructions ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_sender_instruction(sender_email):
    """Delete instructions for a specific sender."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sender_instructions WHERE sender_email = ?", (sender_email.lower(),))
        conn.commit()
    except Exception as e:
        logger.error(f"Error deleting sender instruction: {e}")
    finally:
        conn.close()

def save_instruction(instruction_text, category="general", is_active=True, target="", target_type="", is_critical=False, description=""):
    """Save a new instruction for document processing with extended fields."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO instructions (instruction_text, category, is_active, target, target_type, is_critical, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (instruction_text, category, 1 if is_active else 0, target, target_type, 1 if is_critical else 0, description))
    conn.commit()
    instruction_id = cursor.lastrowid
    conn.close()
    return instruction_id

def get_instructions(category=None, active_only=True, include_test=False):
    """Get instructions, optionally filtered by category."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM instructions"
    params = []
    conditions = []
    if active_only:
        conditions.append("is_active = 1")
    if not include_test:
        conditions.append("is_test_mode = 0")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    if category:
        query += " AND category = ?" if conditions else " WHERE category = ?"
        params.append(category)
    query += " ORDER BY is_critical DESC, created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_instruction_by_id(instruction_id):
    """Get a specific instruction by ID."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM instructions WHERE id = ?", (instruction_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_instruction(instruction_id, instruction_text=None, is_active=None, is_critical=None, status=None, is_test_mode=None, category=None, target=None, target_type=None, description=None):
    """Update an existing instruction with full field support."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    current = get_instruction_by_id(instruction_id)
    if not current:
        conn.close()
        return False
    
    changes = []
    if instruction_text is not None and instruction_text != current.get('instruction_text'):
        changes.append(('instruction_text', current.get('instruction_text'), instruction_text))
        cursor.execute("UPDATE instructions SET instruction_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (instruction_text, instruction_id))
    if is_active is not None and is_active != current.get('is_active'):
        changes.append(('is_active', current.get('is_active'), is_active))
        cursor.execute("UPDATE instructions SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (1 if is_active else 0, instruction_id))
    if is_critical is not None and is_critical != current.get('is_critical'):
        changes.append(('is_critical', current.get('is_critical'), is_critical))
        cursor.execute("UPDATE instructions SET is_critical = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (1 if is_critical else 0, instruction_id))
    if status is not None and status != current.get('status'):
        changes.append(('status', current.get('status'), status))
        cursor.execute("UPDATE instructions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (status, instruction_id))
    if is_test_mode is not None and is_test_mode != current.get('is_test_mode'):
        changes.append(('is_test_mode', current.get('is_test_mode'), is_test_mode))
        cursor.execute("UPDATE instructions SET is_test_mode = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (1 if is_test_mode else 0, instruction_id))
    if category is not None and category != current.get('category'):
        changes.append(('category', current.get('category'), category))
        cursor.execute("UPDATE instructions SET category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (category, instruction_id))
    if target is not None and target != current.get('target'):
        changes.append(('target', current.get('target'), target))
        cursor.execute("UPDATE instructions SET target = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (target, instruction_id))
    if target_type is not None and target_type != current.get('target_type'):
        changes.append(('target_type', current.get('target_type'), target_type))
        cursor.execute("UPDATE instructions SET target_type = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (target_type, instruction_id))
    if description is not None and description != current.get('description'):
        changes.append(('description', current.get('description'), description))
        cursor.execute("UPDATE instructions SET description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (description, instruction_id))
    
    if changes:
        save_revision(instruction_id, changes, "update")
    
    conn.commit()
    conn.close()
    return True

def delete_instruction(instruction_id):
    """Delete an instruction with revision history."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    current = get_instruction_by_id(instruction_id)
    if current:
        save_revision(instruction_id, [('instruction_text', current.get('instruction_text'), None)], "delete")
    cursor.execute("DELETE FROM instructions WHERE id = ?", (instruction_id,))
    conn.commit()
    conn.close()

# Revision History Functions
def save_revision(instruction_id, changes, action="update"):
    """Save a revision to history."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO instruction_revisions (instruction_id, action, changes_json)
        VALUES (?, ?, ?)
    ''', (instruction_id, action, json.dumps(changes)))
    conn.commit()
    conn.close()

def get_revisions(instruction_id=None, limit=50):
    """Get revision history, optionally filtered by instruction_id."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if instruction_id:
        cursor.execute("SELECT * FROM instruction_revisions WHERE instruction_id = ? ORDER BY created_at DESC LIMIT ?", (instruction_id, limit))
    else:
        cursor.execute("SELECT * FROM instruction_revisions ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Dynamic Categories Functions
def get_categories():
    """Get all unique categories from instructions."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM instructions ORDER BY category")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_category(category_name, description=""):
    """Save a new category."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO instruction_categories (category_name, description)
        VALUES (?, ?)
    ''', (category_name, description))
    conn.commit()
    conn.close()

def get_all_categories():
    """Get all categories with descriptions."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM instruction_categories ORDER BY category_name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Auto-init when imported
def seed_default_categories():
    """Seed default instruction categories."""
    default_categories = [
        ("Email - Sender (All)", "Instructions for all emails from a specific sender"),
        ("Email - Sender (Specific)", "Instructions for specific job/subject from sender"),
        ("Email - General Rules", "General email handling rules"),
        ("Document - File Naming", "How to rename and organize files"),
        ("Document - Data Extraction", "What data to extract from documents"),
        ("Document - Routing", "Where to save or send documents"),
        ("Google Sheets - Input", "Logging rules for incoming data"),
        ("Google Sheets - Output", "Reporting and export rules"),
        ("Agents - Accountant", "Instructions for Senior Accountant agent"),
        ("Agents - Auditor", "Instructions for Senior Auditor agent"),
        ("Agents - Admin", "Instructions for Admin Assistant agent"),
        ("Agents - Coach", "Instructions for Communication Coach agent"),
        ("Agents - Marketing", "Instructions for Marketing agent"),
        ("General", "General system instructions"),
    ]
    for name, desc in default_categories:
        save_category(name, desc)

init_db()
seed_default_categories()

# Import and init session/memory tables
try:
    from services.session_manager import init_session_db
    init_session_db()
except Exception as e:
    logger.warning(f"Session manager not available: {e}")
