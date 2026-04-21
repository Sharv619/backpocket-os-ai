#!/usr/bin/env python3
from dotenv import load_dotenv

# Load from the correct .env path
load_dotenv('/home/lade/Hackathons/.git/backpocket-mvp/.env', override=True)

from services.gmail import test_gmail_connection, get_unread_emails

print("=" * 60)
print("🔐 Testing Gmail OAuth Connection")
print("=" * 60)

# Test connection
result = test_gmail_connection()
print(f"\n✅ Connection Test: {result}")

if result['status'] == 'success':
    print(f"📧 Connected as: {result['email_address']}")

    print("\n" + "=" * 60)
    print("📮 Fetching Your Unread Emails")
    print("=" * 60)

    emails = get_unread_emails()
    print(f"\n📬 Found {len(emails)} unread emails:\n")

    for i, email in enumerate(emails, 1):
        print(f"{i}. {email['subject']}")
        print(f"   From: {email['sender']}")
        print(f"   Snippet: {email['snippet'][:100]}...")
        print()
else:
    print(f"\n❌ Connection Failed: {result['message']}")
