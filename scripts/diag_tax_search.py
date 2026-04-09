from services.gmail import get_gmail_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_any_tax():
    service = get_gmail_service()
    logger.info("Searching ALL emails for 'Tax Return'...")
    # Search everywhere (trash/spam included just in case)
    results = service.users().messages().list(userId='me', q='Tax Return', maxResults=10).execute()
    messages = results.get('messages', [])
    if not messages:
        logger.warning("No email found with 'Tax Return' in subject or snippet.")
        return
    
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = m.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        labels = m.get('labelIds', [])
        logger.info(f"MATCH: ID {msg['id']} | Subject: {subject} | Labels: {labels}")

if __name__ == "__main__":
    find_any_tax()
