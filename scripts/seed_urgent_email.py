from services.gmail import get_gmail_service
from email.mime.text import MIMEText
import base64

def send_test_urgent_email():
    service = get_gmail_service()
    
    # We send it to steve@backpocket.os which is one of the brands
    to = "steve@backpocket.os"
    subject = "URGENT: Tax Return Problem"
    body = "Hi Steve, I have a problem with my tax return and need it filed today or I get fined. Please help!"
    
    message = MIMEText(body)
    message['to'] = to
    message['from'] = "support@antigravity-ai.com"
    message['subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"✅ Urgent test email sent to {to}!")
    except Exception as e:
        print(f"❌ Failed to send: {e}")

if __name__ == "__main__":
    send_test_urgent_email()
