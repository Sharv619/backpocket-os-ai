import os
import json
import logging
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
_FALLBACK_TOKEN_DIR = ".gmail_tokens"
_GOOGLE_OAUTH_DEFAULTS = {
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"],
}

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _token_env_keys(token_file: str) -> list[str]:
    base = os.path.basename(token_file)
    stem = base[:-5] if base.endswith('.json') else base

    if stem == "token":
        return ["GMAIL_TOKEN_JSON", "TOKEN_JSON"]

    if stem.startswith("token_"):
        suffix = re.sub(r"[^A-Za-z0-9]+", "_", stem[len("token_"):]).upper()
        return [f"GMAIL_TOKEN_{suffix}_JSON", f"TOKEN_{suffix}_JSON"]

    normalized = re.sub(r"[^A-Za-z0-9]+", "_", stem).upper()
    return [f"GMAIL_{normalized}_JSON", f"{normalized}_JSON"]

def _fallback_token_path(token_file: str) -> str:
    return os.path.join(_FALLBACK_TOKEN_DIR, os.path.basename(token_file))

def get_gmail_token_storage_path(token_file: str) -> str:
    if os.path.isdir(token_file):
        return _fallback_token_path(token_file)
    return token_file

def _extract_json_blob(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return raw[start:end + 1]
    return raw

def _load_json_candidate(raw_or_path: str, source_label: str):
    raw_or_path = (raw_or_path or "").strip()
    if not raw_or_path:
        return None, None

    if os.path.exists(raw_or_path):
        if os.path.isdir(raw_or_path):
            logger.error("Gmail OAuth source '%s' points to a directory, not a JSON file.", raw_or_path)
            return None, None
        with open(raw_or_path, 'r') as f:
            return json.loads(f.read()), f"{source_label}->file:{raw_or_path}"

    return json.loads(_extract_json_blob(raw_or_path)), source_label

def _normalize_oauth_client_config(config: dict) -> dict:
    if not isinstance(config, dict):
        raise ValueError("OAuth config must be a JSON object")

    if config.get("type") == "service_account":
        raise ValueError(
            "Service account JSON cannot be used for Gmail mailbox OAuth. "
            "Use a desktop OAuth client instead."
        )

    if "installed" in config or "web" in config:
        section_name = "installed" if "installed" in config else "web"
        section = dict(config[section_name] or {})
        client_id = section.get("client_id") or section.get("clientId")
        client_secret = section.get("client_secret") or section.get("clientSecret")
        if not client_id or not client_secret:
            raise ValueError("OAuth client config is missing client_id/client_secret")

        section["client_id"] = client_id
        section["client_secret"] = client_secret
        section.setdefault("auth_uri", _GOOGLE_OAUTH_DEFAULTS["auth_uri"])
        section.setdefault("token_uri", _GOOGLE_OAUTH_DEFAULTS["token_uri"])
        section.setdefault(
            "auth_provider_x509_cert_url",
            _GOOGLE_OAUTH_DEFAULTS["auth_provider_x509_cert_url"],
        )
        section.setdefault("redirect_uris", _GOOGLE_OAUTH_DEFAULTS["redirect_uris"])
        return {section_name: section}

    client_id = config.get("client_id") or config.get("clientId")
    client_secret = config.get("client_secret") or config.get("clientSecret")
    if not client_id or not client_secret:
        raise ValueError("OAuth client config is missing client_id/client_secret")

    installed = {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": config.get("auth_uri") or config.get("authUri") or _GOOGLE_OAUTH_DEFAULTS["auth_uri"],
        "token_uri": config.get("token_uri") or config.get("tokenUri") or _GOOGLE_OAUTH_DEFAULTS["token_uri"],
        "auth_provider_x509_cert_url": (
            config.get("auth_provider_x509_cert_url")
            or config.get("authProviderX509CertUrl")
            or _GOOGLE_OAUTH_DEFAULTS["auth_provider_x509_cert_url"]
        ),
        "redirect_uris": config.get("redirect_uris") or config.get("redirectUris") or _GOOGLE_OAUTH_DEFAULTS["redirect_uris"],
    }
    project_id = config.get("project_id") or config.get("projectId")
    if project_id:
        installed["project_id"] = project_id
    return {"installed": installed}

def load_gmail_oauth_client_config():
    candidates = [
        ("GMAIL_OAUTH_JSON", os.getenv("GMAIL_OAUTH_JSON", "").strip()),
        ("GMAIL_CREDENTIALS_JSON", os.getenv("GMAIL_CREDENTIALS_JSON", "").strip()),
        ("GOOGLE_APPLICATION_CREDENTIALS", os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()),
        ("gmail_credentials.json", "gmail_credentials.json"),
    ]

    for source_name, raw_value in candidates:
        if not raw_value:
            continue
        try:
            config, source = _load_json_candidate(raw_value, f"env:{source_name}" if source_name != "gmail_credentials.json" else source_name)
            if config:
                return _normalize_oauth_client_config(config), source
        except json.JSONDecodeError as e:
            logger.error("Error: %s is not valid JSON for Gmail OAuth: %s", source_name, e)
        except ValueError as e:
            logger.error("Error: invalid Gmail OAuth config from %s: %s", source_name, e)

    return None, None

def _load_token_payload(token_file: str):
    token_path_blocked = os.path.isdir(token_file)
    persist_path = get_gmail_token_storage_path(token_file)
    if token_path_blocked:
        logger.error(
            "Gmail token path '%s' is a directory, not a JSON token file. "
            "Using fallback token store '%s'.",
            token_file,
            persist_path,
        )
    elif os.path.exists(token_file):
        with open(token_file, 'r') as f:
            raw = _try_decrypt(f.read().strip())
        return raw, f"file:{token_file}", persist_path

    if persist_path != token_file and os.path.exists(persist_path):
        with open(persist_path, 'r') as f:
            raw = _try_decrypt(f.read().strip())
        return raw, f"file:{persist_path}", persist_path

    for env_key in _token_env_keys(token_file):
        raw = os.getenv(env_key, "").strip()
        if raw:
            logger.info("Using Gmail token from env var %s for %s", env_key, token_file)
            return _try_decrypt(raw), f"env:{env_key}", persist_path

    return None, None, persist_path

def get_gmail_service(token_file='token.json'):
    """Builds and returns the Gmail API service object for a specific token."""
    creds = None
    raw_token, token_source, persist_path = _load_token_payload(token_file)
    if raw_token:
        creds = Credentials.from_authorized_user_info(json.loads(raw_token), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            oauth_config, oauth_source = load_gmail_oauth_client_config()
            if not oauth_config:
                logger.error(
                    "Error: Gmail OAuth config not found. "
                    "Checked GMAIL_OAUTH_JSON, GMAIL_CREDENTIALS_JSON, "
                    "GOOGLE_APPLICATION_CREDENTIALS, and gmail_credentials.json."
                )
                return None
            logger.info("Using Gmail OAuth client config from %s for %s", oauth_source, token_file)
            flow = InstalledAppFlow.from_client_config(oauth_config, SCOPES)
            creds = flow.run_local_server(port=0)

        if persist_path:
            persist_dir = os.path.dirname(persist_path)
            if persist_dir:
                os.makedirs(persist_dir, exist_ok=True)
            with open(persist_path, 'w') as token:
                token.write(_try_encrypt(creds.to_json()))
            if persist_path != token_file:
                logger.info(
                    "Persisted Gmail token for %s to fallback path %s.",
                    token_file,
                    persist_path,
                )

    return build('gmail', 'v1', credentials=creds)

def get_all_account_tokens():
    """Finds all token_*.json files in the root directory, excluding IMAP tokens."""
    tokens = []
    # Always include the primary hub token slot unless the path is corrupted.
    if os.path.isdir('token.json'):
        fallback_path = _fallback_token_path('token.json')
        if os.path.isfile(fallback_path) or any(os.getenv(k, "").strip() for k in _token_env_keys('token.json')):
            tokens.append('token.json')
        else:
            logger.error(
                "Skipping Gmail token slot 'token.json' because it is a directory "
                "and no fallback token payload exists yet."
            )
    else:
        tokens.append('token.json')

    if not os.path.exists('.'): return tokens
    for f in os.listdir('.'):
        # Exclude 'token_imap_' to avoid collision with IMAP module
        if not (f.startswith('token_') and f.endswith('.json')):
            continue
        if f.startswith('token_imap_'):
            continue
        if os.path.isdir(f):
            fallback_path = _fallback_token_path(f)
            if os.path.isfile(fallback_path) or any(os.getenv(k, "").strip() for k in _token_env_keys(f)):
                tokens.append(f)
            else:
                logger.error(
                    "Skipping Gmail token '%s' because it is a directory "
                    "and no fallback token payload exists yet.",
                    f,
                )
            continue
        if os.path.isfile(f):
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
        if os.getenv("DEMO_MODE", "0") == "1":
            logger.info("DEMO_MODE=1: Gmail send skipped for %s", to)
            return {
                "status": "demo",
                "message": f"DEMO_MODE=1: would have sent email to {to}",
            }

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
