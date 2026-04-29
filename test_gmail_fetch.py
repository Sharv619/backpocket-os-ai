import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

token_file = 'token.json'
if os.path.exists(token_file):
    with open(token_file, 'r') as f:
        raw = f.read().strip()
    creds = Credentials.from_authorized_user_info(json.loads(raw))
    service = build('gmail', 'v1', credentials=creds)
    query = 'in:inbox is:unread'
    results = service.users().messages().list(userId='me', q=query, maxResults=50).execute()
    messages = results.get('messages', [])
    for msg in messages:
        msg_details = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_details.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        print(f"ID: {msg['id']} | From: {sender} | Subj: {subject}")
else:
    print("no token")
