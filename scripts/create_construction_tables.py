#!/usr/bin/env python3
"""Create construction/tradie management tables"""

import sqlite3
from datetime import datetime

DB_PATH = "backpocket.db"

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # TABLE 1: Leads
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

    # TABLE 2: Quotes
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

    # TABLE 3: Payments
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

    # TABLE 4: Job Files
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

    # TABLE 5: Site Visits
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

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_lead_id ON quotes(lead_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_quote_id ON payments(quote_id)")

    conn.commit()
    conn.close()

    print("✅ Construction tables created successfully!")

if __name__ == "__main__":
    create_tables()
