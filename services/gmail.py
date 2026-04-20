import os
import sys
import io
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

if sys.platform == 'win32':
    try:
        if sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Optional at-rest encryption for token files. Requires BP_ENCRYPTION_KEY env var.
def _try_encrypt(text: str) -> str:
    try:
        from services.crypto import encrypt_str, is_encrypted
        if not is_encrypted(text):
            return encrypt_str(text)
    except Exception:
        pass
    return text

def _try_decrypt(text: str) -> str:
    try:
        from services.crypto import decrypt_str, is_encrypted
        if is_encrypted(text):
            return decrypt_str(text)
    except Exception:
        pass
    return text

logging.basicConfig(level=logging.INFO, encoding='utf-8')
logger = logging.getLogger(__name__)

def get_gmail_service(token_file='token.json'):
    """Builds and returns the Gmail API service object for a specific token."""
    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            raw = _try_decrypt(f.read().strip())
        creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            oauth_json_str = os.getenv('GMAIL_OAUTH_JSON')

            if oauth_json_str:
                try:
                    oauth_config = json.loads(oauth_json_str)
                    flow = InstalledAppFlow.from_client_config(oauth_config, SCOPES)
                    creds = flow.run_local_server(port=0)
                except json.JSONDecodeError as e:
                    logger.error(f"Error: GMAIL_OAUTH_JSON is not valid JSON: {e}")
                    return None
            elif os.path.exists('gmail_credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file(
                    'gmail_credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                logger.error("Error: GMAIL_OAUTH_JSON env var or gmail_credentials.json not found.")
                return None

        with open(token_file, 'w') as token:
            token.write(_try_encrypt(creds.to_json()))

    return build('gmail', 'v1', credentials=creds)

def get_all_account_tokens():
    """Finds all token_*.json files in the root directory, excluding IMAP tokens."""
    tokens = ['token.json'] # Always include the primary hub
    if not os.path.exists('.'): return tokens
    for f in os.listdir('.'):
        # Exclude 'token_imap_' to avoid collision with IMAP module
        if f.startswith('token_') and f.endswith('.json') and not f.startswith('token_imap_'):
            tokens.append(f)
    return list(set(tokens))

def test_gmail_connection():
    """Tests the connection to the Gmail API."""
    try:
        service = get_gmail_service()
        if not service:
            return {"status": "error", "message": "Gmail credentials not found or flow failed"}
        
        # Call the Gmail API to list basic profile info
        results = service.users().getProfile(userId='me').execute()
        return {"status": "success", "email_address": results.get('emailAddress')}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_unread_emails(token_file='token.json'):
    """Fetches unread emails from the inbox of a specific account."""
    try:
        service = get_gmail_service(token_file)
        if not service:
            return []
        
        # Use in:inbox to catch ALL inbox tabs (Primary, Updates, Forums, etc.)
        # This ensures ATO, ASIC, Stripe and other Tier 2 emails in the Updates tab are never missed.
        query = 'in:inbox is:unread -category:promotions -category:social'
        results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
        messages = results.get('messages', [])
        
        email_data = []
        for msg in messages:
            msg_details = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = msg_details.get('payload', {}).get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            
            # The 'To' header usually preserves the original brand address in forwarding setups.
            # 'Delivered-To' is our backup or the Hub address itself.
            to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), None)
            delivered_to = next((h['value'] for h in headers if h['name'].lower() == 'delivered-to'), None)
            
            brand_identity = to_header if to_header else delivered_to or 'Unknown'
            
            snippet = msg_details.get('snippet', '')
            
            # Detect attachments
            has_attachments = False
            parts = msg_details.get('payload', {}).get('parts', [])
            if not parts and 'body' not in msg_details.get('payload', {}):
                 # Sometimes Gmail returns attachments in a different structure
                 pass
            
            def check_for_attachments(parts_list):
                for p in parts_list:
                    if p.get('filename') and p.get('body', {}).get('attachmentId'):
                        return True
                    if 'parts' in p:
                        if check_for_attachments(p['parts']):
                            return True
                return False
            
            has_attachments = check_for_attachments(parts)

            # Extract clean email addresses
            import re
            email_match_sender = re.search(r'[\w\.-]+@[\w\.-]+', sender)
            clean_sender = email_match_sender.group(0) if email_match_sender else sender
            
            email_match_to = re.search(r'[\w\.-]+@[\w\.-]+', brand_identity)
            clean_to = email_match_to.group(0) if email_match_to else brand_identity
            
            email_data.append({
                "id": msg['id'],
                "threadId": msg['threadId'],
                "subject": subject,
                "sender": sender,
                "clean_email": clean_sender.lower(),
                "delivered_to": clean_to.lower() if clean_to else "unknown", # Accurate Brand Identity
                "snippet": snippet,
                "has_attachments": has_attachments
            })
            
        return email_data
    except Exception as e:
        logger.error(f"Error fetching unread emails: {e}")
        return []

def send_email(to, subject, body_text, from_alias=None, token_file='token.json'):
    """Sends an email using the Gmail API from a specific account token."""
    try:
        service = get_gmail_service(token_file)
        if not service:
            return {"status": "error", "message": f"Gmail service for {token_file} not available"}

        # Validate and clean the recipient email
        to = to.strip()
        if not to or '@' not in to:
            return {"status": "error", "message": f"Invalid recipient: {to}"}
        
        # Clean subject
        subject = subject.strip()
        if subject.lower().startswith('re: re:'):
            subject = subject[6:].strip()
        elif subject.lower().startswith('re:'):
            subject = subject[4:].strip()
        
        from email.mime.text import MIMEText
        import base64

        message = MIMEText(body_text, 'plain', 'utf-8')
        message['to'] = to
        message['subject'] = subject
        
        if from_alias:
            message['from'] = from_alias
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        create_message = {'raw': raw}
        
        send_result = service.users().messages().send(userId='me', body=create_message).execute()
        logger.info(f"Email sent successfully to {to}")
        return {"status": "success", "message_id": send_result.get('id')}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending email: {e}")
        return {"status": "error", "message": error_msg}

def get_historical_context(email_address, max_results=3):
    """
    Searches for past emails from this sender across ALL connected accounts.
    This helps the Twin understand your tone and relationship with the client.
    """
    tokens = get_all_account_tokens()
    all_context = []
    
    for t in tokens:
        try:
            service = get_gmail_service(t)
            if not service: continue
            
            # Search for BOTH sent and received to get the full back-and-forth
            query = f'"{email_address}"'
            results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            for msg in messages:
                msg_data = service.users().messages().get(userId='me', id=msg['id'], format='minimal').execute()
                snippet = msg_data.get('snippet', '')
                # Is it from Steve or the Client?
                label_ids = msg_data.get('labelIds', [])
                role = "Steve" if 'SENT' in label_ids else "Client"
                all_context.append(f"- [{role}]: {snippet}")
                
        except Exception as e:
            logger.error(f"Error fetching historical context from {t}: {e}")
            
    if not all_context:
        return "No past email history found for this contact across all accounts."
        
    return "\n".join(all_context[-5:]) # Return latest 5 context points

def is_replied_to(thread_id, token_file='token.json'):
    """Checks if a thread has any sent messages (replies)."""
    try:
        service = get_gmail_service(token_file)
        if not service:
            return False
            
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        messages = thread.get('messages', [])
        
        for msg in messages:
            # Check if any message in the thread has the 'SENT' label
            if 'SENT' in msg.get('labelIds', []):
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking reply status: {e}")
        return False

def archive_message(msg_id, token_file='token.json'):
    """Removes the INBOX label from a message (Archives it)."""
    try:
        service = get_gmail_service(token_file)
        if not service:
            return False
        service.users().messages().modify(
            userId='me', id=msg_id, 
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Error archiving: {e}")
        return False

def trash_message(msg_id, token_file='token.json'):
    """Moves a message to the Trash."""
    try:
        service = get_gmail_service(token_file)
        if not service:
            return False
        service.users().messages().trash(userId='me', id=msg_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error trashing: {e}")
        return False

def search_emails(query, token_file='token.json', max_results=5):
    """Searches for emails matching a query across Inbox, Archive, and Trash.
    Uses 'fuzzy' logic by searching the term in multiple common fields.
    """
    try:
        service = get_gmail_service(token_file)
        if not service:
            return []
        
        # We try a few search angles to be robust:
        # 1. Exact term anywhere 
        # 2. Part of the from name
        # 3. Part of the subject
        gmail_query = f'"{query}" OR from:{query} OR subject:{query}'
        
        # Include Trash and Spam if specifically searching for missing emails
        results = service.users().messages().list(userId='me', q=gmail_query, maxResults=max_results, includeSpamTrash=True).execute()
        messages = results.get('messages', [])
        
        found_data = []
        for msg in messages:
            try:
                msg_details = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                headers = msg_details.get('payload', {}).get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                snippet = msg_details.get('snippet', '')
                
                found_data.append({
                    "id": msg['id'],
                    "subject": subject,
                    "sender": sender,
                    "snippet": snippet,
                    "token_file": token_file
                })
            except: continue # Skip if individual message read fails
            
        return found_data
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        return []

def rescue_to_inbox(msg_id, token_file='token.json'):
    """Brings a message back to the Inbox and marks it as Unread."""
    try:
        service = get_gmail_service(token_file)
        if not service:
            return False
        
        service.users().messages().modify(
            userId='me', id=msg_id, 
            body={
                'addLabelIds': ['UNREAD', 'INBOX'],
                'removeLabelIds': ['TRASH'] # Remove from trash if it was there
            }
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Error restoring message: {e}")
        return False

def move_to_label(msg_id, label_name, token_file='token.json'):
    """Moves a message to a specific label (creates it if missing)."""
    try:
        service = get_gmail_service(token_file)
        if not service: return False
        
        # 1. Find or Create Label ID
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        label_id = next((l['id'] for l in labels if l['name'].lower() == label_name.lower()), None)
        
        if not label_id:
            # Create it
            logger.info(f"🏷️ Creating new label: {label_name}")
            label_body = {'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
            created = service.users().labels().create(userId='me', body=label_body).execute()
            label_id = created['id']
            
        # 2. Modify Message
        service.users().messages().modify(
            userId='me', id=msg_id, 
            body={'addLabelIds': [label_id], 'removeLabelIds': ['INBOX']}
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Error moving to label {label_name}: {e}")
        return False
