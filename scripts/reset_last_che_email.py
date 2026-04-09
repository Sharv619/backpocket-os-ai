from services.gmail import get_gmail_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_last_email():
    service = get_gmail_service()
    logger.info("Searching for latest email from che.tomenio1@gmail.com...")
    results = service.users().messages().list(userId='me', q='from:che.tomenio1@gmail.com').execute()
    messages = results.get('messages', [])
    if not messages:
        logger.warning("No emails found from this sender.")
        return

    # Take the two most recent ones (just in case)
    for msg in messages[:2]:
        msg_id = msg['id']
        logger.info(f"Marking message {msg_id} as UNREAD and INBOX...")
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [msg_id],
                'addLabelIds': ['UNREAD', 'INBOX'],
                'removeLabelIds': []
            }
        ).execute()
    
    logger.info("Success! The latest emails are now UNREAD.")

if __name__ == "__main__":
    reset_last_email()
