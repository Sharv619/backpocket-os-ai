from services.gmail import get_gmail_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_specific_email():
    logger.info("Deep search for 'Tax Return' in last 100 emails...")
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', maxResults=100).execute()
    messages = results.get('messages', [])
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = m.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        if "tax return" in subject.lower():
            logger.info(f"MATCH FOUND! ID: {msg['id']} | Subject: {subject} | Snippet: {m['snippet']}")

if __name__ == "__main__":
    find_specific_email()
