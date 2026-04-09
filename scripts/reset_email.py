from services.gmail import get_gmail_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_test_email():
    service = get_gmail_service()
    logger.info("Searching for 'Test email' from che.tomenio1@gmail.com...")
    results = service.users().messages().list(userId='me', q='from:che.tomenio1@gmail.com subject:"Test email"').execute()
    messages = results.get('messages', [])
    if not messages:
        logger.warning("Email not found.")
        return

    msg_id = messages[0]['id']
    logger.info(f"Marking message {msg_id} as UNREAD...")
    service.users().messages().batchModify(
        userId='me',
        body={
            'ids': [msg_id],
            'addLabelIds': ['UNREAD']
        }
    ).execute()
    logger.info("Success! The email is now UNREAD.")

if __name__ == "__main__":
    reset_test_email()
