#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv('/home/lade/Hackathons/.git/backpocket-mvp/.env', override=True)

from services.gmail import get_unread_emails
from services.gemini import triage_email, draft_response
import services.database as db
import uuid
from datetime import datetime

print("=" * 70)
print("📥 IMPORTING REAL EMAILS INTO BACKPOCKET")
print("=" * 70)

# Get all unread emails
emails = get_unread_emails()
print(f"\n✅ Fetched {len(emails)} real emails from Gmail\n")

# Clear demo data first
conn = db.sqlite3.connect(db.DB_PATH)
cursor = conn.cursor()
cursor.execute("DELETE FROM pending_approvals")
conn.commit()
print("🗑️  Cleared demo data\n")

# Import each email
imported = 0
for i, email in enumerate(emails, 1):
    try:
        # Generate ref_id
        ref_id = f"EMAIL-{str(uuid.uuid4())[:8].upper()}"

        # Determine tier based on sender/domain
        sender_domain = email['clean_email'].split('@')[1] if '@' in email['clean_email'] else 'unknown'

        # Tier assignment logic
        if 'linkedin' in sender_domain:
            tier = 4
        elif 'substack' in sender_domain or 'newsletter' in sender_domain.lower():
            tier = 5
        elif any(x in sender_domain for x in ['github', 'vercel', 'twine']):
            tier = 2
        else:
            tier = 3

        # Generate AI draft response first
        draft_body = f"[Tier {tier} - Auto-draft pending review]"
        try:
            email_dict = {
                "subject": email['subject'],
                "sender": email['sender'],
                "snippet": email['snippet']
            }
            draft_result = draft_response(
                email_content=email_dict,
                tier=tier
            )
            if draft_result and isinstance(draft_result, str):
                draft_body = draft_result
        except Exception as e:
            draft_body = f"[Draft error: {str(e)[:50]}]"

        # Insert into pending_approvals with draft
        cursor.execute("""
            INSERT INTO pending_approvals
            (ref_id, sender, subject, draft_body, tier, delivered_to, message_id, thread_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ref_id,
            email['sender'],
            email['subject'],
            draft_body,
            tier,
            email['delivered_to'],
            email['id'],
            email['threadId'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        imported += 1
        print(f"✓ {i:2d}. {ref_id} | Tier {tier} | {email['subject'][:50]}")

    except Exception as e:
        print(f"✗ {i:2d}. ERROR: {str(e)[:60]}")

conn.close()

print("\n" + "=" * 70)
print(f"✅ IMPORT COMPLETE: {imported}/{len(emails)} emails imported")
print("=" * 70)
print("\n🚀 Your dashboard is now populated with REAL data!")
print("   → http://127.0.0.1:8000/static/index.html")
