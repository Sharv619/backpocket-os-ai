import asyncio
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter
import services.database as db
from app.models.schemas import SenderInstructionRequest

logger = logging.getLogger(__name__)
router = APIRouter()


def generate_ref_id():
    prefix = datetime.now().strftime("%Y-%m")

    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ref_id FROM (
            SELECT ref_id FROM pending_approvals
            UNION ALL
            SELECT ref_id FROM action_history
            UNION ALL
            SELECT ref_id FROM corrections
        )
        WHERE ref_id LIKE ?
        ORDER BY ref_id DESC
        LIMIT 1
        """,
        (f"{prefix}-%",),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        last_id = row[0]
        try:
            last_num = int(last_id.split("-")[2])
            new_num = last_num + 1
        except Exception as e:
            logger.warning(f"Error parsing last ID {last_id}, starting from 1: {e}")
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}-{new_num:05d}"


@router.get("/api/pending")
async def get_pending():
    try:
        conn = db.sqlite3.connect(db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ref_id, sender, subject, tier, delivered_to, created_at FROM pending_approvals ORDER BY created_at DESC LIMIT 20"
        )
        rows = cursor.fetchall()
        conn.close()

        items = []
        for row in rows:
            items.append(
                {
                    "ref_id": row[0],
                    "sender": row[1],
                    "subject": row[2],
                    "tier": row[3],
                    "delivered_to": row[4],
                    "created_at": row[5],
                }
            )

        return {"count": len(items), "items": items}
    except Exception as e:
        logger.error(f"Error fetching pending: {e}")
        return {"count": 0, "items": [], "error": str(e)}


@router.get("/api/email-rules")
async def get_email_rules():
    try:
        try:
            from services.google_sheets import get_priority_list

            priority_list = get_priority_list()
        except Exception:
            priority_list = {}

        golden_senders = [
            "jco064690@gmail.com",
            "trustdeed.com.au",
            "gjcctax.au",
            "cqstax.com",
            "almemmolos@gmail.com",
            "johnwatts.com.au",
            "david@vdmandthorn.com",
            "che.tomenio1@gmail.com",
        ]

        tier_2_senders = [
            "ato.gov.au",
            "asic.gov.au",
            "site_managersinstitute.com",
            "site_managersintitute.com",
            "publicestimators.org.au",
            "ifpa.com.au",
            "ndiscommission.gov.au",
            "stripe.com",
            "cloudoffis",
        ]

        rules = {
            "tier_definitions": {
                "1": "REPLY NEEDED - Important client emails requiring personalized response",
                "2": "REVIEW NEEDED - Non-urgent but needs acknowledgment",
                "3": "FYI ONLY - Info emails, no response needed",
                "4": "ARCHIVE - Portal updates, digests, auto-generated emails",
                "5": "LOW PRIORITY - Newsletters, promotions, spam-like",
            },
            "golden_senders": golden_senders,
            "tier_2_senders": tier_2_senders,
            "priority_list": priority_list,
            "processing_layers": [
                "Layer 0: Whitelist override (known clients always = Tier 1)",
                "Layer 1: Pre-triage rules (Suitedash, onboarding, etc.)",
                "Layer 2: AI Triage (Gemini decides tier)",
            ],
        }
        return rules
    except Exception as e:
        logger.error(f"Get email rules error: {e}")
        return {"error": str(e)}


@router.post("/api/sender-instruction")
async def api_save_sender_instruction(request: SenderInstructionRequest):
    db.save_sender_instruction(
        request.sender_email, request.instructions, request.category
    )

    try:
        from services.google_sheets import sync_instructions_to_sheets

        all_instructions = db.get_all_sender_instructions()
        sync_instructions_to_sheets(all_instructions)
    except Exception as e:
        logger.error(f"Could not sync to Sheets: {e}")

    return {
        "status": "success",
        "message": f"Instructions saved for {request.sender_email}",
    }


@router.get("/api/sender-instructions")
async def api_get_sender_instructions():
    instructions = db.get_all_sender_instructions()
    return {"instructions": instructions}


@router.post("/api/sync-instructions-to-sheets")
async def api_sync_instructions():
    instructions = db.get_all_sender_instructions()
    try:
        from services.google_sheets import sync_instructions_to_sheets

        sync_instructions_to_sheets(instructions)
        return {
            "status": "success",
            "message": f"Synced {len(instructions)} instructions to Sheets",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/api/sender-instruction/{sender_email}")
async def api_get_sender_instruction(sender_email: str):
    instruction = db.get_sender_instruction(sender_email)
    if instruction:
        return instruction
    return {"message": "No instructions found"}


@router.delete("/api/sender-instruction/{sender_email}")
async def api_delete_sender_instruction(sender_email: str):
    db.delete_sender_instruction(sender_email)
    return {"status": "success", "message": f"Instruction deleted for {sender_email}"}


async def handle_slash_command(
    message: str, conversation_id: str, context_data: dict
) -> Optional[str]:
    import re

    parts = message.split(" ", 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "/pending":
        pending_refs = db.get_all_pending_refs()
        if not pending_refs:
            return "No pending approvals. Your inbox is clear!"
        lines = ["PENDING APPROVALS:\n"]
        for ref in pending_refs[:10]:
            if ref.startswith("FIND-"):
                continue
            p = db.get_pending_approval(ref)
            if p:
                lines.append(f"**#{ref}** - {p.get('subject', 'No Subject')[:50]}")
                lines.append(f"_From: {p.get('sender', 'Unknown')}_\n")
        return "\n".join(lines)

    elif cmd == "/approve":
        if not args:
            return "Usage: `/approve <ref>` (e.g., `/approve 2026-04-00001`)"
        ref_id = args.strip()
        info = db.get_pending_approval(ref_id)
        if not info:
            return f"Ref #{ref_id} not found."
        from services.gmail import send_email

        email_addr = info.get("sender", "")
        subject = info.get("subject", "")
        draft = info.get("draft_body", "")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, send_email, email_addr, f"Re: {subject}", draft
        )
        if result.get("status") == "success":
            db.log_action(
                ref_id, "approved", info.get("tier", ""), "Dashboard slash command"
            )
            db.delete_pending_approval(ref_id)
            return f"Email sent to {email_addr} (Ref: {ref_id})"
        return f"Send failed: {result.get('message', 'Unknown error')}"

    elif cmd == "/revise":
        match = re.match(r"/revise\s+(\S+)\s+(.+)", message)
        if not match:
            return "Usage: `/revise <ref> <feedback>` (e.g., `/revise 2026-04-00001 make it friendlier`)"
        ref_id, feedback = match.groups()
        info = db.get_pending_approval(ref_id)
        if not info:
            return f"Ref #{ref_id} not found."
        from services.gemini import refine_draft

        original = info["draft_body"]
        email_obj = {
            "id": info["message_id"],
            "subject": info["subject"],
            "sender": info["sender"],
        }
        loop = asyncio.get_running_loop()
        new_draft = await loop.run_in_executor(
            None, refine_draft, email_obj, original, feedback
        )
        info["draft_body"] = new_draft
        db.save_pending_approval(ref_id, info)
        return f"**Revised (Ref: {ref_id})**\n\n{new_draft[:500]}..."

    elif cmd == "/coach":
        ref_id = args.strip() if args else None
        if not ref_id:
            return "Usage: `/coach <ref>` (e.g., `/coach 2026-04-00001`)"
        info = db.get_pending_approval(ref_id)
        if not info:
            return f"Ref #{ref_id} not found."
        from services.gemini import analyze_draft_with_coach

        draft = info.get("draft_body", "")
        email_content = {"subject": info.get("subject", ""), "snippet": ""}
        analysis = analyze_draft_with_coach(email_content, draft)
        if analysis and isinstance(analysis, dict):
            score = analysis.get("score", "N/A")
            feedback = analysis.get("feedback", "No detailed feedback")
            tone = analysis.get("tone", "N/A")
            return f"**Communication Coach Analysis (Ref: {ref_id})**\n\n**Score:** {score}/100\n**Tone:** {tone}\n\n**Feedback:** {feedback}"
        return "Could not analyze draft."

    elif cmd == "/help":
        return """**Available Commands:**

`/pending` - Show all pending approvals
`/approve <ref>` - Send email (e.g., `/approve 2026-04-00001`)
`/revise <ref> <feedback>` - AI revise draft
`/coach <ref>` - Run Communication Coach analysis
`/status` - Show system status
`/help` - Show this help

Just type naturally - Twin understands everything!"""

    elif cmd == "/status":
        pending_count = len(
            [r for r in db.get_all_pending_refs() if not r.startswith("FIND-")]
        )
        history = db.get_action_history(5)
        recent = (
            f"{history[0]['action']} #{history[0]['ref_id']}"
            if history
            else "No recent actions"
        )
        return f"""**System Status**

- **Twin:** Online & Ready
- **Pending Approvals:** {pending_count}
- **Last Action:** {recent}
- **Server:** Running on port 8000"""

    return None
