from fastapi import APIRouter
import logging
import os
import asyncio
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import services.database as db
from services.gmail import send_email

router = APIRouter(prefix="/api/mobile", tags=["mobile"])
logger = logging.getLogger(__name__)

_TIER_LABELS = {"1": "URGENT", "2": "HIGH", "3": "MEDIUM", "4": "LOW", "5": "SPAM"}


@router.get("/pending")
async def mobile_pending():
    """Return pending emails in a simplified format for mobile clients."""
    try:
        conn = __import__("sqlite3").connect(db.DB_PATH, timeout=10)
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute(
            "SELECT ref_id, sender, subject, draft_body, tier, created_at "
            "FROM pending_approvals WHERE status = 'pending' ORDER BY tier, created_at DESC"
        )
        rows = cur.fetchall()
        conn.close()

        now = datetime.utcnow()
        items = []
        for r in rows:
            try:
                created = datetime.strptime(r["created_at"][:19], "%Y-%m-%d %H:%M:%S")
                age_hours = round((now - created).total_seconds() / 3600, 1)
            except Exception:
                age_hours = 0
            items.append(
                {
                    "ref_id": r["ref_id"],
                    "sender": r["sender"],
                    "subject": r["subject"],
                    "tier": int(r["tier"]) if r["tier"] else 3,
                    "tier_label": _TIER_LABELS.get(str(r["tier"]), "MEDIUM"),
                    "preview": (r["draft_body"] or "")[:120],
                    "age_hours": age_hours,
                }
            )
        return {"count": len(items), "items": items}
    except Exception as e:
        logger.error(f"mobile_pending error: {e}")
        return {"count": 0, "items": [], "error": str(e)}


class MobileApproveRequest(BaseModel):
    ref_id: str
    note: Optional[str] = None


@router.post("/approve")
async def mobile_approve(request: MobileApproveRequest):
    """Approve a pending email from a mobile client. Respects DEMO_MODE."""
    ref_id = request.ref_id
    info = db.get_pending_approval(ref_id)
    if not info:
        return {"status": "error", "message": f"Ref {ref_id} not found"}

    sender = info.get("sender", "unknown")
    subject = info.get("subject", "")
    tier = info.get("tier", "3")

    if os.getenv("DEMO_MODE", "0") == "1":
        db.log_action(
            ref_id, "approved_demo", tier, request.note or "mobile approve (demo)"
        )
        return {
            "status": "demo",
            "ref_id": ref_id,
            "message": f"DEMO MODE: would have sent draft to {sender}",
        }

    # Real mode: mirror the desktop /api/approve logic exactly
    email_addr = sender.strip()
    draft = info.get("draft_body", "")
    delivered_to = info.get("delivered_to", "")
    loop = asyncio.get_running_loop()

    if not email_addr or "@" not in email_addr:
        return {"status": "error", "message": f"Invalid recipient: '{email_addr}'"}

    # Clean up "Re: Re:" duplication
    clean_subject = subject
    if clean_subject.lower().startswith("re: re:"):
        clean_subject = clean_subject[6:].strip()
    elif clean_subject.lower().startswith("re:"):
        clean_subject = clean_subject[4:].strip()

    # AUTO-MATCH TOKEN based on delivered_to account
    if "|" in delivered_to:
        actual_alias, token_source = delivered_to.split("|", 1)
    elif delivered_to:
        actual_alias = delivered_to
        if "yourwebaccountant" in delivered_to.lower():
            token_source = "token_ywa.json"
        elif "bigbossaccountants" in delivered_to.lower():
            token_source = "token_imap_admin.json"
        elif "bigbossgroup" in delivered_to.lower():
            token_source = "token.json"
        else:
            token_source = "token.json"
    else:
        actual_alias, token_source = None, "token.json"

    try:
        if token_source.startswith("token_imap_"):
            from services.imap import send_email_smtp

            result = await loop.run_in_executor(
                None,
                send_email_smtp,
                token_source,
                email_addr,
                f"Re: {clean_subject}",
                draft,
            )
        else:
            result = await loop.run_in_executor(
                None,
                send_email,
                email_addr,
                f"Re: {clean_subject}",
                draft,
                actual_alias,
                token_source,
            )

        if result.get("status") == "success":
            db.log_action(
                ref_id, "approved_mobile", tier, request.note or "mobile approve"
            )
            db.save_correction(
                ref_id,
                "approve",
                draft,
                draft,
                "Approved via mobile",
                sender=email_addr,
                subject=clean_subject,
            )
            db.delete_pending_approval(ref_id)

            # WhatsApp notification
            try:
                from services.whapi import send_whatsapp_message

                founder_phone = os.getenv("FOUNDER_PHONE") or ""
                if founder_phone:
                    await loop.run_in_executor(
                        None,
                        send_whatsapp_message,
                        founder_phone,
                        f"✅ *EMAIL SENT (Mobile)*\n\nTo: {email_addr}\nSubject: {clean_subject}\n\nRef: {ref_id}",
                    )
            except Exception:
                pass

            return {
                "status": "approved",
                "ref_id": ref_id,
                "message": f"Draft sent to {email_addr} (Re: {clean_subject})",
            }
        else:
            return {"status": "error", "message": result.get("message", "Send failed")}
    except Exception as e:
        logger.error(f"mobile_approve send error: {e}")
        return {"status": "error", "message": str(e)}


class MobileChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


@router.post("/chat")
async def mobile_chat(request: MobileChatRequest):
    """Lightweight twin chat endpoint for mobile clients."""
    try:
        from services.gemini import get_gemini_client
        from services.twin_brain import build_twin_context

        client = get_gemini_client()
        if not client:
            return {
                "response": "AI not available — check GEMINI_API_KEY.",
                "conversation_id": "",
            }

        context = ""
        try:
            context = build_twin_context()
        except Exception:
            pass

        system_prompt = (
            "You are BackPocket Twin, an AI assistant for Steve, an Australian accountant "
            "who manages emails for sole traders and tradies. Be concise and helpful.\n\n"
            f"{context}"
        )

        from google.genai import types as genai_types

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=request.message,
            config=genai_types.GenerateContentConfig(system_instruction=system_prompt),
        )
        reply = response.text or "Sorry, no response generated."
        return {
            "response": reply,
            "conversation_id": request.conversation_id or "",
        }
    except Exception as e:
        logger.error(f"mobile_chat error: {e}")
        return {"response": f"Error: {str(e)}", "conversation_id": ""}
