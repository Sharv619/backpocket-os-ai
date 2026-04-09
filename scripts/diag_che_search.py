from services.gmail import get_gmail_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_che():
    service = get_gmail_service()
    logger.info("Searching for emails from che.tomenio1@gmail.com...")
    results = service.users().messages().list(userId='me', q='from:che.tomenio1@gmail.com').execute()
    messages = results.get('messages', [])
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = m.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        labels = m.get('labelIds', [])
        logger.info(f"SENDER MATCH: ID {msg['id']} | Subject: {subject} | Labels: {labels} | Snippet: {m['snippet'][:50]}")

if __name__ == "__main__":
    find_che()
