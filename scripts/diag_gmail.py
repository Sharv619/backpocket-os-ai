from services.gmail import get_unread_emails
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_tax_email():
    logger.info("Searching for 'Tax Return' in unread emails...")
    emails = get_unread_emails()
    found = False
    for email in emails:
        if "tax return" in email['subject'].lower() or "tax return" in email['snippet'].lower():
            logger.info(f"FOUND! ID: {email['id']} | Subject: {email['subject']} | Sender: {email['sender']}")
            found = True
    if not found:
        logger.info("Email not found in the UNREAD list.")

if __name__ == "__main__":
    find_tax_email()
