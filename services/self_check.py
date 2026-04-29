import os
import sys
import io
import logging
from services.database import get_stale_approvals, mark_nudged
from services.whapi import send_whatsapp_message, test_whapi_connection
from services.gemini import OWNER_NAME
from services.gmail import test_gmail_connection
from services.google_sheets import test_sheets_connection, get_todays_portal_updates
from services.gemini import test_gemini_connection

if sys.platform == 'win32':
    try:
        if sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, encoding='utf-8')
logger = logging.getLogger(__name__)

def run_self_check():
    """
    Scans for stale Tier 1 approvals and performs health checks.
    This is the Twin's 'Conscience'.
    """
    try:
        # 1. Check for stale approvals (Nudges for Urgent Emails)
        stale_items = get_stale_approvals(hours=4)
        if stale_items:
            founder_phone = os.getenv("FOUNDER_PHONE")
            if founder_phone:
                clean_phone = "".join(filter(str.isdigit, founder_phone))
                for item in stale_items:
                    # We only nudge if it's Tier 1 (Urgent)
                    if item.get('tier') == '1':
                        thread_id = item.get('thread_id')
                        delivered_to = item.get('delivered_to', 'token.json')
                        token_file = delivered_to.split('|')[-1] if '|' in delivered_to else 'token.json'
                        
                        # --- SILENT CHECK: Did founder already reply in Gmail? ---
                        from services.gmail import is_replied_to
                        if thread_id and not token_file.startswith('token_imap_'): # Only check Gmail threads for now
                            if is_replied_to(thread_id, token_file):
                                logger.info(f"🧘 Found manual reply for Ref #{item['ref_id']}. Removing from waitlist.")
                                from services.database import delete_pending_approval
                                delete_pending_approval(item['ref_id'])
                                continue

                        msg = f"🔔 *Urgent Nudge* — Ref *#{item['ref_id']}*\n"
                        msg += f"Client *{item['sender']}* is waiting for a reply to: _{item['subject']}_\n\n"
                        msg += "It has been pending for over 4 hours. Tap to approve or ask for a rewrite! 🚀"
                        send_whatsapp_message(clean_phone, msg)
                        mark_nudged(item['ref_id'])
                        logger.info(f"Nudged founder for Ref #{item['ref_id']}")

    except Exception as e:
        logger.error(f"Error in self-check: {e}")

def send_morning_pulse():
    """Sends a summary of systems health and pending tasks to the founder."""
    try:
        founder_phone = os.getenv("FOUNDER_PHONE")
        if not founder_phone:
            logger.warning("Morning Pulse skipped: FOUNDER_PHONE not set.")
            return

        # Connectivity Checks
        gmail_status = test_gmail_connection()
        sheets_status = test_sheets_connection()
        gemini_status = test_gemini_connection()
        whapi_status = test_whapi_connection()
        
        from services.database import get_all_pending_refs
        pending_count = len(get_all_pending_refs())
        portal_count = get_todays_portal_updates()
        
        pulse_msg = "☀️ *BackPocket Twin: Morning Pulse*\n\n"
        
        all_green = (gmail_status['status'] == 'success' and 
                     sheets_status['status'] == 'success' and 
                     gemini_status['status'] == 'success')
        
        pulse_msg += f"{'🟢' if all_green else '⚠️'} *Systems*: {'All system go!' if all_green else 'Some issues detected.'}\n"
        pulse_msg += f"- Gmail: {'✅' if gmail_status['status'] == 'success' else '❌'}\n"
        pulse_msg += f"- Sheets: {'✅' if sheets_status['status'] == 'success' else '❌'}\n"
        pulse_msg += f"- AI Brain: {'✅' if gemini_status['status'] == 'success' else '❌'}\n"
        pulse_msg += f"- WhatsApp Link: {'✅' if whapi_status['status'] == 'success' else '❌'}\n\n"
        
        pulse_msg += f"📋 *Waitlist*: There are *{pending_count}* tasks awaiting your approval.\n"
        
        if portal_count > 0:
            pulse_msg += f"🤫 *Notifications*: *{portal_count}* platform updates were logged silently to your sheet today.\n\n"
        else:
            pulse_msg += "\n"
            
        pulse_msg += f"Zero-cost & Scalable. Have a productive day, {OWNER_NAME}! 🚀"
        
        clean_phone = "".join(filter(str.isdigit, founder_phone))
        send_whatsapp_message(clean_phone, pulse_msg)
        logger.info("Morning pulse sent to founder.")
        
    except Exception as e:
        logger.error(f"Error sending morning pulse: {e}")
