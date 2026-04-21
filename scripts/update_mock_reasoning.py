import sqlite3
import json

DB_PATH = "backpocket.db"

def update_mock_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Manually ensure columns exist
    try:
        cursor.execute("ALTER TABLE pending_approvals ADD COLUMN ai_reasoning TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE pending_approvals ADD COLUMN suggested_actions TEXT")
    except sqlite3.OperationalError:
        pass
        
    # 1. Update Leaking tap
    cursor.execute("""
        UPDATE pending_approvals 
        SET ai_reasoning = 'This client needs an urgent response as it is a plumbing emergency. I matched this with your previous pricing for Parramatta call-outs.',
            suggested_actions = ?
        WHERE ref_id = '2026-04-DEMO01'
    """, (json.dumps([{"action": "add_to_calendar", "label": "Schedule Parramatta Visit"}]),))
    
    # 2. Update Kitchen renovation
    cursor.execute("""
        UPDATE pending_approvals 
        SET ai_reasoning = 'High-value lead. Customer mentioned a specific budget of $18k. I drafted a polite request for a site visit to lock in the quote.',
            suggested_actions = ?
        WHERE ref_id = '2026-04-DEMO02'
    """, (json.dumps([{"action": "create_lead", "label": "Promote to CRM Lead"}]),))
    
    # 3. Update Timber deck
    cursor.execute("""
        UPDATE pending_approvals 
        SET ai_reasoning = 'Routine maintenance request. I calculated the material costs based on current Merbau prices from Bunnings.',
            suggested_actions = ?
        WHERE ref_id = '2026-04-DEMO03'
    """, (json.dumps([{"action": "order_materials", "label": "Draft Bunnings Order"}]),))

    conn.commit()
    conn.close()
    print("✅ Mock data updated with AI reasoning and actions!")

if __name__ == "__main__":
    update_mock_data()
