import sqlite3
import os

db_path = 'backpocket.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT count(*) FROM pending_approvals')
    count = cursor.fetchone()[0]
    print(f"Pending approvals: {count}")
    
    cursor.execute('SELECT sender, subject FROM pending_approvals LIMIT 5')
    rows = cursor.fetchall()
    print("\nSample emails in database:")
    for row in rows:
        print(f"From: {row[0]} | Subject: {row[1]}")
    conn.close()
else:
    print(f"Database {db_path} not found")
