from services.whapi import send_whatsapp_message
import os
from dotenv import load_dotenv

load_dotenv()
phone = os.getenv("FOUNDER_PHONE")
clean_phone = "".join(filter(str.isdigit, phone))

print(f"Testing WhatsApp to {clean_phone}...")
res = send_whatsapp_message(clean_phone, "📟 *BACKPOCKET DIAGNOSTICS*\n\nIf you see this, the WhatsApp bridge is officially ALIVE and RESPONSIVE. System is now scanning for your 'Tax Return' email.")
print(res)
