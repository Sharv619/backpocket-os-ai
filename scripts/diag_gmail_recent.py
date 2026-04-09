from services.gmail import get_gmail_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_recent():
    logger.info("Checking most recent 5 emails (Read or Unread)...")
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = m.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        logger.info(f"Subject: {subject} | From: {sender} | Snippet: {m['snippet'][:50]}")

if __name__ == "__main__":
    check_recent()
