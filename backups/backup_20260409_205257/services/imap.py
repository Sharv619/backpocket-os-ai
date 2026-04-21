import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

def clean_html(raw_html):
    """Strip HTML tags from email body to get plain text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator="\n")
    # Clean up excessive newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def decode_mime_words(s):
    """Decode email subject encoded strings."""
    if not s:
        return ""
    try:
        return ''.join(
            word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
            for word, encoding in decode_header(s)
        )
    except Exception:
        return str(s)

def extract_email_address(full_address):
    """Extract just the email part from 'Name <email@domain.com>'"""
    if not full_address:
        return ""
    match = re.search(r'<([^>]+)>', full_address)
    return match.group(1).lower() if match else full_address.strip().lower()

def connect_imap(config):
    """Establish IMAP connection using config dict."""
    try:
        mail = imaplib.IMAP4_SSL(config['imap_host'], int(config['imap_port']))
        mail.login(config['username'], config['password'])
        return mail
    except Exception as e:
        logger.error(f"IMAP Connection failed for {config['username']}: {e}")
        return None

def get_unread_emails_imap(config_file):
    """Fetch unread emails via IMAP. Emulates the output of get_unread_emails for Gmail."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        mail = connect_imap(config)
        if not mail:
            return []
            
        mail.select("inbox")
        status, response = mail.search(None, "UNSEEN")
        unread_emails = []
        
        if status == "OK":
            mail_ids = response[0].split()
            for i in mail_ids:
                # Fetch RFC822 format (the whole email)
                status, msg_data = mail.fetch(i, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject = decode_mime_words(msg["Subject"])
                        sender = decode_mime_words(msg.get("From", ""))
                        clean_sender = extract_email_address(sender)
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(errors='ignore')
                                        break
                                elif content_type == "text/html" and "attachment" not in content_disposition:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        html_body = payload.decode(errors='ignore')
                                        body = clean_html(html_body)
                        else:
                            content_type = msg.get_content_type()
                            payload = msg.get_payload(decode=True)
                            if payload:
                                decoded_payload = payload.decode(errors='ignore')
                                if content_type == "text/html":
                                    body = clean_html(decoded_payload)
                                else:
                                    body = decoded_payload
                            else:
                                body = ""
                                
                        # Use the IMAP UID or sequence ID as the message ID. We'll use sequence ID here to uniquely identify for actions.
                        msg_id = i.decode('utf-8')
                        
                        # Generate thread id mock (we don't have true thread ids in standard IMAP like Gmail does)
                        thread_id = msg.get("Message-ID", f"mock_thread_{msg_id}").strip("<>")
                        
                        # Detect attachments
                        has_attachments = False
                        for part in msg.walk():
                            if part.get_content_disposition() == 'attachment':
                                has_attachments = True
                                break

                        email_obj = {
                            "id": f"imap_{config['username']}_{msg_id}",
                            "threadId": thread_id,
                            "subject": subject,
                            "snippet": body[:500] if body else "",
                            "sender": sender,
                            "clean_email": clean_sender,
                            "delivered_to": config['username'],
                            "raw_imap_id": msg_id,
                            "source_type": "imap",
                            "config_file": config_file,
                            "has_attachments": has_attachments
                        }
                        unread_emails.append(email_obj)
                        
        mail.close()
        mail.logout()
        return unread_emails
    except Exception as e:
        logger.error(f"Error fetching IMAP unread for {config_file}: {e}")
        return []

def send_email_smtp(config_file, to_email, subject, body_text):
    """Sends an email using standard SMTP."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        msg = MIMEMultipart()
        msg['From'] = config['username']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        server = smtplib.SMTP_SSL(config['smtp_host'], int(config['smtp_port']))
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
        return {"status": "success", "message": "Email sent via SMTP"}
        
    except Exception as e:
        logger.error(f"Failed to send email via SMTP for {config_file}: {e}")
        return {"status": "error", "message": str(e)}

def archive_message_imap(msg_id_string, config_file):
    """Moves a message to the Archive folder."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Parse our custom ID: imap_user@domain.com_34
        if not msg_id_string.startswith("imap_"):
            return # Safety check
            
        parts = msg_id_string.split('_')
        raw_imap_id = parts[-1]
        
        mail = connect_imap(config)
        if not mail: return
        
        mail.select("inbox")
        
        # Check if archive folder exists, copy, then delete original
        status, folders = mail.list()
        archive_name = "Archive"
        if status == "OK" and folders:
            for f in folders:
                if f and b'Archive' in f:
                    try:
                        decoded_f = f.decode()
                        parts = decoded_f.split(' "/" ')
                        if len(parts) == 2:
                            archive_name = parts[1].strip('"')
                            break
                    except Exception:
                        continue
        
        # Copy to archive
        result = mail.copy(raw_imap_id, archive_name)
        if result[0] == 'OK':
            # Mark original as deleted
            mail.store(raw_imap_id, '+FLAGS', '\\Deleted')
            mail.expunge()
            logger.info(f"Archived IMAP message {raw_imap_id}")
        else:
            # Fallback: Just mark as read
            mail.store(raw_imap_id, '+FLAGS', '\\Seen')
            
        mail.close()
        mail.logout()
    except Exception as e:
        logger.error(f"IMAP Archive failed: {e}")

def trash_message_imap(msg_id_string, config_file):
    """Moves a message to Trash or deletes it."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        if not msg_id_string.startswith("imap_"):
            return
            
        parts = msg_id_string.split('_')
        raw_imap_id = parts[-1]
        
        mail = connect_imap(config)
        if not mail: return
        
        mail.select("inbox")
        mail.store(raw_imap_id, '+FLAGS', '\\Deleted')
        mail.expunge()
        logger.info(f"Trashed IMAP message {raw_imap_id}")
            
        mail.close()
        mail.logout()
    except Exception as e:
        logger.error(f"IMAP Trash failed: {e}")

def get_all_imap_configs():
    """Finds all token_imap_*.json files."""
    tokens = []
    try:
        for filename in os.listdir('.'):
            if filename.startswith('token_imap_') and filename.endswith('.json'):
                tokens.append(filename)
    except Exception as e:
        logger.error(f"Error finding IMAP tokens: {e}")
    return tokens
