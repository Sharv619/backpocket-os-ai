import sqlite3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def delete_pending_approval(ref_id):
    conn = sqlite3.connect('backpocket.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_approvals WHERE ref_id = ?", (ref_id,))
    conn.commit()
    conn.close()
    print(f"Deleted Ref #{ref_id}")

def send_whatsapp_message(to_number, text):
    token = os.getenv("WHAPI_TOKEN")
    url = "https://gate.whapi.cloud/messages/text"
    payload = {"to": to_number, "body": text}
    headers = {"accept": "application/json", "authorization": f"Bearer {token}"}
    r = requests.post(url, json=payload, headers=headers)
    print(f"Sent WhatsApp status to {to_number}: {r.status_code}")

phone = "".join(filter(str.isdigit, os.getenv("FOUNDER_PHONE", "")))
ids_to_ignore = ['7204', '4251', '7232', '1408', '0630', '7314', '0243', '1085', '2039', '6756']

for rid in ids_to_ignore:
    delete_pending_approval(rid)
    send_whatsapp_message(phone, f"🗑️ *Ref #{rid}* marked as ignore and removed (Manual override).")

print("Manual ignore cleanup complete.")
