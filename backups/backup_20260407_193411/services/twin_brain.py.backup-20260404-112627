"""
Twin Brain - Central knowledge system for the Twin AI
Gives Twin access to all instructions, data, and tools
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"


def get_connection():
    return sqlite3.connect(DB_PATH, timeout=10)


def get_all_instructions():
    """Load ALL system instructions from database"""
    conn = get_connection()
    cur = conn.cursor()
    
    instructions = []
    try:
        cur.execute("""
            SELECT id, instruction_text, category, target, target_type, 
                   is_critical, is_test_mode, is_active, created_at, updated_at
            FROM instructions 
            WHERE is_active = 1
            ORDER BY is_critical DESC, id
        """)
        rows = cur.fetchall()
        
        for row in rows:
            instructions.append({
                "id": row[0],
                "instruction": row[1],
                "category": row[2],
                "target": row[3],
                "target_type": row[4],
                "is_critical": bool(row[5]),
                "is_test_mode": bool(row[6]),
                "is_active": bool(row[7]),
                "created_at": row[8],
                "updated_at": row[9]
            })
    except Exception as e:
        logger.error(f"Error loading instructions: {e}")
    finally:
        conn.close()
    
    return instructions


def get_sender_instructions():
    """Load sender-specific instructions"""
    conn = get_connection()
    cur = conn.cursor()
    
    instructions = []
    try:
        cur.execute("""
            SELECT id, sender_email, category, instructions, 
                   is_critical, created_at, updated_at
            FROM sender_instructions
            ORDER BY is_critical DESC, sender_email
        """)
        rows = cur.fetchall()
        
        for row in rows:
            instructions.append({
                "id": row[0],
                "sender": row[1],
                "category": row[2],
                "instructions": row[3],
                "is_critical": bool(row[4]),
                "created_at": row[5],
                "updated_at": row[6]
            })
    except Exception as e:
        logger.error(f"Error loading sender instructions: {e}")
    finally:
        conn.close()
    
    return instructions


def get_pending_approvals():
    """Load all pending approvals"""
    conn = get_connection()
    cur = conn.cursor()
    
    pending = []
    try:
        cur.execute("""
            SELECT ref_id, sender, subject, tier, status, created_at
            FROM pending_approvals
            WHERE status = 'pending'
            ORDER BY created_at DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        
        for row in rows:
            pending.append({
                "ref_id": row[0],
                "sender": row[1],
                "subject": row[2],
                "tier": row[3],
                "status": row[4],
                "created_at": row[5]
            })
    except Exception as e:
        logger.error(f"Error loading pending: {e}")
    finally:
        conn.close()
    
    return pending


def get_action_history(limit=20):
    """Load recent action history"""
    conn = get_connection()
    cur = conn.cursor()
    
    history = []
    try:
        cur.execute(f"""
            SELECT ref_id, action, tier, notes, created_at
            FROM action_history
            ORDER BY created_at DESC
            LIMIT {limit}
        """)
        rows = cur.fetchall()
        
        for row in rows:
            history.append({
                "ref_id": row[0],
                "action": row[1],
                "tier": row[2],
                "notes": row[3],
                "created_at": row[4]
            })
    except Exception as e:
        logger.error(f"Error loading history: {e}")
    finally:
        conn.close()
    
    return history


def get_recent_corrections(limit=10):
    """Load recent corrections/feedback from Cherry"""
    conn = get_connection()
    cur = conn.cursor()
    
    corrections = []
    try:
        cur.execute(f"""
            SELECT ref_id, sender, subject, correction_type, 
                   original_draft, corrected_draft, feedback, created_at
            FROM corrections
            ORDER BY created_at DESC
            LIMIT {limit}
        """)
        rows = cur.fetchall()
        
        for row in rows:
            corrections.append({
                "ref_id": row[0],
                "sender": row[1],
                "subject": row[2],
                "type": row[3],
                "original": row[4],
                "corrected": row[5],
                "feedback": row[6],
                "created_at": row[7]
            })
    except Exception as e:
        logger.error(f"Error loading corrections: {e}")
    finally:
        conn.close()
    
    return corrections


def get_system_stats():
    """Get system statistics"""
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {}
    try:
        cur.execute("SELECT COUNT(*) FROM processed_messages")
        stats["emails_processed"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pending_approvals WHERE status = 'pending'")
        stats["pending_approvals"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM instructions WHERE is_active = 1")
        stats["active_instructions"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM sender_instructions")
        stats["sender_instructions"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM action_history")
        stats["actions_taken"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM corrections")
        stats["corrections_given"] = cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Error loading stats: {e}")
    finally:
        conn.close()
    
    return stats


def build_twin_context(sender_email=None, category=None):
    """Build smart, filtered context for Twin to prevent context bloat."""
    
    # Get all data but filter intelligently
    instructions = get_all_instructions()
    sender_instructions = get_sender_instructions()
    pending = get_pending_approvals()
    history = get_action_history()
    corrections = get_recent_corrections()
    stats = get_system_stats()
    
    # 🧠 SMART FILTER: Only include relevant generic instructions
    filtered_instructions = []
    for i in instructions:
        if i['is_critical']:
            filtered_instructions.append(i)
        elif category and i['category'].lower() == category.lower():
            filtered_instructions.append(i)
        # Always include a max of 5 general rules if no category
        elif len(filtered_instructions) < 5:
            filtered_instructions.append(i)

    # 🧠 SMART FILTER: Only include relevant sender instructions
    filtered_sender_inst = []
    if sender_email:
        filtered_sender_inst = [s for s in sender_instructions if s['sender'].lower() == sender_email.lower()]
    else:
        # Just top 3 critical ones
        filtered_sender_inst = [s for s in sender_instructions if s['is_critical']][:3]

    # Format instructions for context
    instructions_text = "\n\n".join([
        f"[{i['category']}] {'(CRITICAL) ' if i['is_critical'] else ''}{i['instruction'][:500]}"
        for i in filtered_instructions
    ])
    
    # Format sender instructions
    sender_text = "\n".join([
        f"- {s['sender']} ({s['category']}): {s['instructions'][:200]}..."
        for s in filtered_sender_inst
    ])
    
    # Format pending
    pending_text = "\n".join([
        f"- #{p['ref_id']}: {p['subject'][:60]}... from {p['sender']} (Tier {p['tier']})"
        for p in pending[:10]
    ])
    
    # Format history
    history_text = "\n".join([
        f"- {h['action']} #{h['ref_id']} (Tier {h['tier']}): {h['notes'] or ''} - {h['created_at']}"
        for h in history[:10]
    ])
    
    # Build the context
    context = f"""
=== CHERRY'S BACKPOCKET TWIN KNOWLEDGE BASE ===

SYSTEM STATS:
- Emails Processed: {stats.get('emails_processed', 0)}
- Pending Approvals: {stats.get('pending_approvals', 0)}
- Active Instructions: {stats.get('active_instructions', 0)}
- Sender Instructions: {stats.get('sender_instructions', 0)}
- Actions Taken: {stats.get('actions_taken', 0)}
- Corrections Given: {stats.get('corrections_given', 0)}

=== ACTIVE SYSTEM INSTRUCTIONS ===
{instructions_text}

=== SENDER-SPECIFIC INSTRUCTIONS ===
{sender_text}

=== PENDING APPROVALS ===
{pending_text if pending_text else "No pending approvals - inbox is clear!"}

=== RECENT ACTIVITY ===
{history_text if history_text else "No recent activity"}

=== RECENT CORRECTIONS (Learning from Cherry) ===
"""
    
    for c in corrections[:5]:
        context += f"""
- Ref #{c['ref_id']}: {c['type']} feedback on email from {c['sender']}
  Original issue: {c['feedback'] or 'N/A'}
"""
    
    return context


def get_conversation_summary():
    """Get recent conversation history for context"""
    conn = get_connection()
    cur = conn.cursor()
    
    messages = []
    try:
        cur.execute("""
            SELECT role, message, created_at 
            FROM conversation_memory 
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        rows = cur.fetchall()
        
        for row in reversed(rows):
            messages.append({
                "role": row[0],
                "message": row[1],
                "time": row[2]
            })
    except Exception:
        pass
    finally:
        conn.close()
    
    return messages


def add_twin_message(role, message):
    """Add a message to conversation memory"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO conversation_memory (role, message, created_at)
            VALUES (?, ?, datetime('now'))
        """, (role, message[:2000]))
        conn.commit()
    except Exception as e:
        logger.error(f"Error adding twin message: {e}")
    finally:
        conn.close()
