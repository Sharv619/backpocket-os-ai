#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from services.gemini import draft_response

# Test with a sample email
email_content = {
    "subject": "Invoice #2024-001 - $1,500",
    "sender": "accounts@supplier.com",
    "snippet": "Hi there, we've sent the invoice for your recent order. Please find the details attached. Payment is due within 30 days."
}

print("=" * 70)
print("🧪 TESTING DRAFT GENERATION WITH OPENROUTER")
print("=" * 70)
print(f"\nEmail Subject: {email_content['subject']}")
print(f"From: {email_content['sender']}")
print(f"Snippet: {email_content['snippet'][:100]}...\n")

try:
    print("📝 Generating draft...")
    draft = draft_response(email_content=email_content, tier=1)

    if draft and isinstance(draft, str):
        print(f"\n✅ SUCCESS! Draft generated:\n")
        print(f"---\n{draft}\n---")
    else:
        print(f"\n❌ FAILED: Draft returned as {type(draft).__name__}")
        print(f"Value: {draft}")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
