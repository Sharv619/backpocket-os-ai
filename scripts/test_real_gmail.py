import os
from dotenv import load_dotenv
from services.gmail import get_unread_emails

load_dotenv()

def test_gmail_fetch():
    print("🚀 Testing Gmail fetch with real credentials...")
    token_file = "token.json"
    if not os.path.exists(token_file):
        print(f"❌ Error: {token_file} not found!")
        return

    try:
        emails = get_unread_emails(token_file)
        print(f"✅ Success! Found {len(emails)} unread emails.")
        for i, email in enumerate(emails[:3]):
            print(f"  [{i+1}] From: {email.get('sender')}")
            print(f"      Subject: {email.get('subject')}")
    except Exception as e:
        print(f"❌ Gmail fetch failed: {e}")

if __name__ == "__main__":
    test_gmail_fetch()
