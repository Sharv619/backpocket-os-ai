import os
import sys
import io
import requests
import logging
import datetime
from typing import Dict, Any, Optional, List

if sys.platform == 'win32':
    try:
        if sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format='%(message)s', encoding='utf-8')

logger = logging.getLogger(__name__)

WHAPI_API_URL = "https://gate.whapi.cloud/messages/text"
WHAPI_BUTTONS_URL = "https://gate.whapi.cloud/messages/interactive"
FAILED_QUEUE_PATH = "logs/failed_whatsapp_queue.txt"


def format_phone_number(phone: str) -> str:
    """Ensure phone number is in correct WhatsApp format (digits + @s.whatsapp.net)."""
    if not phone:
        return phone
    # Strip all non-digit characters
    clean_phone = "".join(filter(str.isdigit, phone))
    if not clean_phone.endswith('@s.whatsapp.net'):
        clean_phone += '@s.whatsapp.net'
    return clean_phone


class WhatsAppService:
    def __init__(self):
        self.token = os.getenv("WHAPI_TOKEN", "")
        if not self.token:
            logger.warning("WHAPI_TOKEN not set in environment variables.")
        self.headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        # Ensure backup folder exists
        os.makedirs(os.path.dirname(FAILED_QUEUE_PATH), exist_ok=True)

    def _write_to_local_queue(self, to_number: str, text: str, reason: str = "Unknown") -> bool:
        """Save failed messages to a local backup file so no notification is ever truly lost."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            separator = "=" * 60
            entry = (
                f"\n{separator}\n"
                f"TIMESTAMP : {timestamp}\n"
                f"RECIPIENT : {to_number}\n"
                f"FAIL REASON: {reason}\n"
                f"MESSAGE:\n{text}\n"
                f"{separator}\n"
            )
            with open(FAILED_QUEUE_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
            logger.info(f"💾 Failed message backed up to {FAILED_QUEUE_PATH}")
            return True
        except Exception as e:
            logger.error(f"❌ Could not save backup: {e}")
            return False

    def send_message(self, to_number: str, text: str) -> Dict[str, Any]:
        """Send a plain-text WhatsApp message with automatic phone formatting."""
        if not self.token:
            logger.error("❌ WHAPI_TOKEN not set. Cannot send WhatsApp message.")
            return {"status": "error", "message": "WHAPI_TOKEN not configured"}

        formatted_phone = format_phone_number(to_number)
        if not formatted_phone:
            logger.error("❌ Invalid phone number provided.")
            return {"status": "error", "message": "Invalid phone number"}

        logger.info(f"📱 Sending WhatsApp message to {formatted_phone}")
        payload = {
            "typing_time": 0,
            "to": formatted_phone,
            "body": text
        }

        try:
            response = requests.post(WHAPI_API_URL, json=payload, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"WhatsApp sent! ID: {data.get('message', {}).get('id', 'unknown')}")
                return {"status": "success", "data": data}
            else:
                response_text = response.text or ""
                reason = f"HTTP {response.status_code}: {response_text[:200]}"
                logger.error(f"❌ WhatsApp send failed: {reason}")
                self._write_to_local_queue(to_number, text, reason)
                return {"status": "error", "message": reason}
        except requests.exceptions.Timeout:
            reason = "Timeout after 15s"
            logger.error("❌ WhatsApp send timed out.")
            self._write_to_local_queue(to_number, text, reason)
            return {"status": "error", "message": reason}
        except Exception as e:
            reason = f"Error: {str(e)}"
            logger.error(f"❌ WhatsApp send error: {e}")
            self._write_to_local_queue(to_number, text, reason)
            return {"status": "error", "message": reason}

    def send_buttons(self, to_number: str, text: str, buttons: list) -> Dict[str, Any]:
        """Send an interactive button message via Whapi."""
        if not self.token:
            return {"status": "error", "message": "WHAPI_TOKEN not configured"}

        formatted_phone = format_phone_number(to_number)
        payload = {
            "to": formatted_phone,
            "type": "button",
            "body": {"text": text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons
                ]
            }
        }
        try:
            response = requests.post(WHAPI_BUTTONS_URL, json=payload, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"WhatsApp buttons sent to {formatted_phone}")
                return {"status": "success", "data": data}
            else:
                response_text = response.text or ""
                logger.error(f"❌ Button send failed: {response.status_code} {response_text[:200]}")
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Button send error: {e}")
            return {"status": "error", "message": str(e)}

    def send_notification(self, email_summary: Dict, tier: int, ai_draft: str, ref_id: str = "????") -> Dict[str, Any]:
        """Send a T1/T2 email notification to Steve with draft and approval shortcuts."""
        try:
            founder_phone = os.getenv("FOUNDER_PHONE", "")
            if not founder_phone:
                logger.error("❌ FOUNDER_PHONE not set.")
                return {"status": "error", "message": "FOUNDER_PHONE not configured"}

            delivered_to = email_summary.get('delivered_to', 'Unknown')
            # Strip the stored token suffix (e.g. "info@bps.com.au|token.json" → "info@bps.com.au")
            if '|' in delivered_to:
                delivered_to = delivered_to.split('|')[0]

            tier_emoji = "🌟" if tier == 1 else "🏛️"
            body = (
                f"{tier_emoji} *BackPocket Twin — Ref #{ref_id}*\n"
                f"🏷️ Tier {tier} | _{email_summary.get('subject', 'No Subject')}_\n\n"
                f"👤 *From:* {email_summary.get('sender', 'Unknown')}\n"
                f"📮 *To:* {delivered_to}\n\n"
                f"📝 *AI Draft Preview:*\n{str(ai_draft)[:300]}...\n\n"
                f"✅ Reply: *approve {ref_id}*\n"
                f"🔄 Reply: *revise {ref_id}: your feedback*\n"
                f"🆕 Reply: *add {ref_id}* (add to client master)\n"
                f"📋 Reply: *draft {ref_id}* (get full draft)"
            )
            return self.send_message(founder_phone, body)
        except Exception as e:
            logger.error(f"❌ send_notification error: {e}")
            return {"status": "error", "message": str(e)}

    def send_daily_email_summary(self, pending_refs: Optional[List] = None, archived_today: Optional[List] = None, trashed_today: Optional[List] = None) -> Dict[str, Any]:
        """
        Send Steve a daily summary of ALL email activity by tier.
        - pending_refs: list of pending approval ref IDs (T1/T2 drafts)
        - archived_today: list of dicts with subject/sender/tier for T3/T4 archived
        - trashed_today: list of dicts for T5 trashed
        """
        try:
            pending_refs = pending_refs or []
            archived_today = archived_today or []
            trashed_today = trashed_today or []
            
            founder_phone = os.getenv("FOUNDER_PHONE", "")
            if not founder_phone:
                return {"status": "error", "message": "FOUNDER_PHONE not configured"}

            now = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            lines = [f"📊 *BackPocket Daily Summary* — {now}\n"]

            # T1/T2 Pending Drafts
            if pending_refs:
                lines.append(f"🌟 *{len(pending_refs)} Drafts Awaiting Approval (T1/T2):*")
                for rid in pending_refs[:10]:
                    lines.append(f"  • Ref #{rid}")
                if len(pending_refs) > 10:
                    lines.append(f"  ... and {len(pending_refs) - 10} more")
            else:
                lines.append("✅ *No pending drafts* — inbox clear!")

            lines.append("")

            # T3/T4 Archived
            archived = archived_today or []
            if archived:
                lines.append(f"🗃️ *{len(archived)} Emails Archived Today (T3/T4):*")
                for item in archived[:8]:
                    lines.append(f"  • [{item.get('tier','?')}] {item.get('subject','?')[:40]} — _{item.get('sender','?')[:25]}_")
            else:
                lines.append("🗃️ *No emails archived today.*")

            lines.append("")

            # T5 Trashed
            trashed = trashed_today or []
            if trashed:
                lines.append(f"🗑️ *{len(trashed)} Emails Trashed Today (T5/Spam):*")
                for item in trashed[:5]:
                    lines.append(f"  • {item.get('subject','?')[:40]}")
            else:
                lines.append("🗑️ *No spam trashed today.*")

            lines.append("")
            lines.append("🔍 Reply *pending* to list all drafts.\nReply *find <name>* to search any email.")

            body = "\n".join(lines)
            return self.send_message(founder_phone, body)
        except Exception as e:
            logger.error(f"❌ send_daily_email_summary error: {e}")
            return {"status": "error", "message": str(e)}

    def test_connection(self) -> Dict[str, Any]:
        """Test the WhatsApp API connection by sending a test message to the founder."""
        founder_phone = os.getenv("FOUNDER_PHONE", "")
        if not founder_phone:
            return {"status": "error", "message": "FOUNDER_PHONE not configured"}
        result = self.send_message(founder_phone, "🧪 *BackPocket Connection Test* — WhatsApp is working! ✅")
        return result


# ── Global singleton ──────────────────────────────────────────────────
whatsapp_service = WhatsAppService()


# ── Module-level convenience functions (used throughout main.py) ──────

def send_whatsapp_message(to_number: str, text: str) -> Dict[str, Any]:
    """Send a plain WhatsApp message. Safe to call from sync or async (via run_in_executor)."""
    return whatsapp_service.send_message(to_number, text)


def send_notification(email_summary: Dict, tier: int, ai_draft: str, ref_id: str = "????") -> Dict[str, Any]:
    """Send a T1/T2 notification to Steve with draft and approval shortcuts."""
    return whatsapp_service.send_notification(email_summary, tier, ai_draft, ref_id)


def send_daily_email_summary(pending_refs: Optional[List] = None, archived_today: Optional[List] = None, trashed_today: Optional[List] = None) -> Dict[str, Any]:
    """Send Steve's daily email activity summary by tier."""
    return whatsapp_service.send_daily_email_summary(pending_refs or [], archived_today or [], trashed_today or [])


# ── Scheduled message helpers (called from main.py background_scheduler) ──

def send_pending_items_summary():
    """4 PM daily: Send summary of pending approval drafts + today's archived/trashed emails."""
    import services.database as db
    pending_refs = [r for r in db.get_all_pending_refs() if not r.startswith("FIND-")]
    
    # Get today's history
    today_history = db.get_action_history(limit=50)
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    today_actions = [h for h in today_history if h.get('created_at', '').startswith(today)]
    
    approved = [h for h in today_actions if h.get('action') == 'approved']
    logged = [h for h in today_actions if h.get('action') == 'archived']
    revised = [h for h in today_actions if h.get('action') == 'revised']
    
    founder_phone = os.getenv("FOUNDER_PHONE", "")
    if not founder_phone:
        return
        
    lines = [f"📊 *BackPocket Afternoon Summary* — {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n"]
    
    if pending_refs:
        lines.append(f"⏳ *{len(pending_refs)} Pending:*")
        for r in pending_refs[:5]:
            lines.append(f"  • Ref #{r}")
        if len(pending_refs) > 5:
            lines.append(f"  ... and {len(pending_refs) - 5} more")
    else:
        lines.append("✅ No pending emails!")
    
    lines.append("")
    lines.append("📈 *Today Processed:*")
    lines.append(f"  ✅ Approved: {len(approved)}")
    lines.append(f"  📋 Logged/Archived: {len(logged)}")
    lines.append(f"  🔄 Revised: {len(revised)}")
    
    msg = "\n".join(lines)
    send_whatsapp_message(founder_phone, msg)


def send_morning_nudge():
    """8 AM daily: Remind Steve of any overnight pending drafts."""
    import services.database as db
    pending_refs = [r for r in db.get_all_pending_refs() if not r.startswith("FIND-")]
    founder_phone = os.getenv("FOUNDER_PHONE", "")
    if not founder_phone:
        return
    
    
    if pending_refs:
        lines = ["☀️ *Good morning, Steve!*\n"]
        lines.append(f"You have *{len(pending_refs)} email(s)* waiting for review:\n")
        
        # Group by tier
        tier1 = [r for r in pending_refs if r.startswith('2026') and any(db.get_pending_approval(r).get('tier') == '1' for r in [r])]
        
        for r in pending_refs[:8]:
            p = db.get_pending_approval(r)
            tier = p.get('tier', '?') if p else '?'
            subject = p.get('subject', '')[:35] if p else ''
            lines.append(f"  • Ref #{r} [{tier}] {subject}")
        
        if len(pending_refs) > 8:
            lines.append(f"  ... and {len(pending_refs) - 8} more")
            
        lines.append("\n💡 Reply *pending* to see all, or open dashboard for details.")
        msg = "\n".join(lines)
    else:
        msg = "☀️ *Good morning, Steve!* 🎉 Your inbox is clear — no pending emails!"
    
    send_whatsapp_message(founder_phone, msg)


def send_spam_bulk_ask():
    """Optional: Ask Steve if there's bulk spam to clear (can be expanded later)."""
    pass


def test_whapi_connection() -> Dict[str, Any]:
    """Test the WhatsApp API connection — used by diagnostics and self_check."""
    return whatsapp_service.test_connection()
