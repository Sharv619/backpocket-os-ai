import os
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter
import services.database as db
from app.models.schemas import (
    ApproveRequest,
    ReviseRequest,
    SaveDraftRequest,
    ArchiveRequest,
    AddClientRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/approve")
async def api_approve(request: ApproveRequest):
    ref_id = request.ref_id
    loop = asyncio.get_running_loop()
    info = db.get_pending_approval(ref_id)
    if not info:
        return {"status": "error", "message": f"Ref #{ref_id} not found"}

    email_addr = info.get("sender", "").strip()
    subject = info.get("subject", "")
    draft = info.get("draft_body", "")

    if os.getenv("DEMO_MODE", "0") == "1":
        db.log_action(
            ref_id, "approved_demo", info.get("tier", ""), "demo mode - no real send"
        )
        return {
            "status": "demo",
            "message": f"DEMO MODE: draft for {email_addr} approved (not sent). Set DEMO_MODE=0 for real sends.",
            "ref_id": ref_id,
            "draft_preview": draft[:200],
        }

    try:
        from services.hooks import run_hook

        hook_data = {
            "ref_id": ref_id,
            "draft_body": draft,
            "subject": subject,
            "sender": email_addr,
            "tier": info.get("tier", ""),
        }
        run_hook("pre_approval", hook_data)
    except Exception:
        pass

    if not email_addr or email_addr == "unknown sender" or "@" not in email_addr:
        return {
            "status": "error",
            "message": f"Cannot send - invalid recipient: '{email_addr}'. Please check the sender address.",
        }

    if subject.lower().startswith("re: re:"):
        subject = subject[6:].strip()
    elif subject.lower().startswith("re:"):
        subject = subject[4:].strip()

    delivered_to = info.get("delivered_to", "")
    if "|" in delivered_to:
        actual_alias, token_source = delivered_to.split("|", 1)
    elif delivered_to:
        actual_alias = delivered_to
        if "yourwebestimator" in delivered_to.lower():
            token_source = "token_ywa.json"
        elif "bigbossestimators" in delivered_to.lower():
            token_source = "token_imap_admin.json"
        elif "bigbossgroup" in delivered_to.lower():
            token_source = "token.json"
        else:
            token_source = "token.json"
    else:
        actual_alias, token_source = None, "token.json"

    from services.gmail import send_email

    if token_source.startswith("token_imap_"):
        from services.imap import send_email_smtp

        result = await loop.run_in_executor(
            None, send_email_smtp, token_source, email_addr, f"Re: {subject}", draft
        )
    else:
        result = await loop.run_in_executor(
            None,
            send_email,
            email_addr,
            f"Re: {subject}",
            draft,
            actual_alias,
            token_source,
        )

    if result["status"] == "success":
        from services.google_sheets import log_activity

        await loop.run_in_executor(
            None,
            log_activity,
            {"email_address": email_addr, "status": f"Dashboard Approved (#{ref_id})"},
        )
        db.log_action(
            ref_id, "approved", info.get("tier", ""), "Approved from dashboard"
        )
        db.save_correction(
            ref_id,
            "approve",
            draft,
            draft,
            "Approved as-is",
            sender=email_addr,
            subject=subject,
        )

        try:
            from services.twin_engine import rag, TwinType

            rag.ingest(TwinType.ADMIN, f"approved-{ref_id}", (
                f"APPROVED DRAFT (human-validated):\n"
                f"To: {email_addr}\nSubject: {subject}\nDraft:\n{draft}"
            ), {
                "source": "approved_draft",
                "ref_id": ref_id,
                "sender": email_addr,
                "subject": subject,
            })
        except Exception:
            pass

        db.delete_pending_approval(ref_id)

        try:
            from services.hooks import run_hook

            hook_data = {
                "ref_id": ref_id,
                "action": "approved",
                "draft_body": draft,
                "subject": subject,
                "sender": email_addr,
                "tier": info.get("tier", ""),
            }
            run_hook("post_approval", hook_data)
        except Exception:
            pass

        from services.whapi import send_whatsapp_message

        founder_phone = os.getenv("FOUNDER_PHONE") or ""
        if founder_phone:
            await loop.run_in_executor(
                None,
                send_whatsapp_message,
                founder_phone,
                f"EMAIL SENT\n\nTo: {email_addr}\nSubject: {subject}\n\nRef: {ref_id}",
            )

        return {"status": "success", "message": f"Email sent to {email_addr}"}
    else:
        return {"status": "error", "message": result.get("message", "Send failed")}


@router.post("/api/archive")
async def api_archive_pending(request: ArchiveRequest):
    ref_id = request.ref_id
    should_archive = request.archive
    info = db.get_pending_approval(ref_id)
    if not info:
        return {"status": "error", "message": f"Ref #{ref_id} not found"}

    from services.google_sheets import log_activity
    from services.whapi import send_whatsapp_message

    loop = asyncio.get_running_loop()

    tier = info.get("tier", "")
    sender = info.get("sender", "")
    subject = info.get("subject", "")

    if tier == "4" or "portal" in sender.lower() or "suitedash" in sender.lower():
        await loop.run_in_executor(
            None,
            log_activity,
            {
                "email_address": sender,
                "subject": subject,
                "body": info.get("draft_body", ""),
                "tier": "4",
                "status": "Portal Update - Check portal",
            },
            "Portal_Updates",
        )

        phone = os.getenv("FOUNDER_PHONE", "")
        if phone:
            await loop.run_in_executor(
                None,
                send_whatsapp_message,
                phone,
                f"Portal Update: {subject}\nCheck Suitedash portal for details.",
            )
    else:
        status_msg = (
            f"Logged {'& Archived' if should_archive else 'Logged Only'} (#{ref_id})"
        )
        await loop.run_in_executor(
            None,
            log_activity,
            {
                "email_address": sender,
                "subject": subject,
                "body": info.get("draft_body", ""),
                "tier": tier,
                "status": status_msg,
            },
        )

    db.log_action(
        ref_id,
        "archived",
        tier,
        f"{'Archived' if should_archive else 'Logged, kept in inbox'} from dashboard",
    )

    if should_archive:
        db.delete_pending_approval(ref_id)

    return {
        "status": "success",
        "message": f"Ref #{ref_id} {('logged to Portal_Updates + WhatsApp sent' if tier == '4' else 'logged and archived')}",
    }


@router.post("/api/revise")
async def api_revise(request: ReviseRequest):
    ref_id = request.ref_id
    loop = asyncio.get_running_loop()
    info = db.get_pending_approval(ref_id)
    if not info:
        return {"status": "error", "message": f"Ref #{ref_id} not found"}

    original = info["draft_body"]
    feedback = request.feedback or request.comment or "Edited"

    if request.new_draft:
        new_draft = request.new_draft
        info["draft_body"] = new_draft
        db.save_pending_approval(ref_id, info)
        db.save_correction(ref_id, "revise", original, new_draft, feedback)

        try:
            from services.twin_engine import rag, TwinType

            rag.ingest(TwinType.ADMIN, f"revision-{ref_id}", (
                f"REVISION (user corrected AI draft):\n"
                f"Sender: {info.get('sender', '')}\nSubject: {info.get('subject', '')}\n"
                f"Original: {original[:300]}\n"
                f"Corrected: {new_draft[:500]}\n"
                f"Feedback: {feedback}"
            ), {
                "source": "revision",
                "ref_id": ref_id,
                "feedback": feedback,
            })
        except Exception:
            pass

        return {"status": "success", "new_draft": new_draft, "message": "Draft saved"}

    if not request.comment:
        return {"status": "error", "message": "Provide either new_draft or comment"}

    from services.gemini import refine_draft

    email_obj = {
        "id": info["message_id"],
        "threadId": info["thread_id"],
        "subject": info["subject"],
        "sender": info["sender"],
    }
    new_draft = await loop.run_in_executor(
        None, refine_draft, email_obj, original, request.comment
    )
    info["draft_body"] = new_draft
    db.save_pending_approval(ref_id, info)
    db.save_correction(ref_id, "revise", original, new_draft, request.comment)
    return {"status": "success", "new_draft": new_draft}


@router.post("/api/save-draft")
async def api_save_draft(request: SaveDraftRequest):
    ref_id = request.ref_id
    draft_body = request.draft_body
    if not db.get_pending_approval(ref_id):
        return {"status": "error", "message": f"Ref #{ref_id} not found"}
    db.update_draft_body(ref_id, draft_body)
    return {"status": "success", "message": "Draft saved"}


@router.get("/api/drafts")
async def api_get_drafts():
    conn = db.sqlite3.connect(db.DB_PATH)
    conn.row_factory = db.sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_approvals ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"drafts": [dict(r) for r in rows]}


@router.get("/api/draft/{ref_id}")
async def api_get_draft(ref_id: str):
    draft = db.get_draft(ref_id)
    if not draft:
        return {"status": "error", "message": f"Draft #{ref_id} not found"}
    return {"draft": draft}


@router.post("/api/add-client")
async def api_add_client(request: AddClientRequest):
    ref_id = request.ref_id

    if not request.email:
        info = db.get_pending_approval(ref_id)
        if not info:
            return {"status": "error", "message": f"Ref #{ref_id} not found"}
        email = info.get("sender", "")
    else:
        email = request.email

    if not request.first_name:
        request.first_name = (
            email.split("@")[0].replace(".", " ").title() if email else "New"
        )

    from services.google_sheets import add_new_client_to_master

    loop = asyncio.get_running_loop()

    client_data = {
        "from_name": f"{request.first_name} {request.last_name}".strip(),
        "email_address": email,
        "mobile": request.mobile,
        "background_info": request.background_info or f"Added from Ref #{ref_id}",
    }

    await loop.run_in_executor(None, add_new_client_to_master, client_data)
    db.delete_pending_approval(ref_id)

    return {
        "status": "success",
        "message": f"Client added: {request.first_name} {request.last_name}",
    }


@router.post("/api/add-client-from-email")
async def api_add_client_from_email(request: ApproveRequest):
    ref_id = request.ref_id
    info = db.get_pending_approval(ref_id)
    if not info:
        return {"status": "error", "message": f"Ref #{ref_id} not found"}

    from services.gemini import get_gemini_client

    client = get_gemini_client()
    if not client:
        return {"status": "error", "message": "Gemini not available"}

    raw_email_body = (
        info.get("email_body") or info.get("draft_body") or "No content available"
    )
    email_content = f"Sender: {info.get('sender')}\nSubject: {info.get('subject')}\n\nFull Email Content:\n{raw_email_body}"

    prompt = f"""You need to extract client information from this email.

SCAN THE EMAIL CAREFULLY FOR:
1. SIGNATURE BLOCK - name, title, company, phone, email
2. CONTACT DETAILS - phone numbers
3. NAME - First AND Last name from signature

Return this exact JSON format:
{{
  "first_name": "First name only",
  "last_name": "Last name only",
  "email": "Their email address from signature",
  "mobile": "PHONE NUMBER with format 0412 345 678",
  "client_status": "New",
  "estimator_or_site_manager": "",
  "birthdate": "",
  "background_info": "2-3 sentences about who they are"
}}

EMAIL:
{email_content}

Extract all details - especially look for phone numbers in signature blocks!"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    try:
        import json

        response_text = response.text.strip() if response and response.text else "{}"
        client_info = json.loads(response_text)
    except Exception as e:
        logger.error(f"Failed to parse client info from AI response: {e}")
        return {"status": "error", "message": "Could not parse AI response"}

    from services.google_sheets import add_new_client_to_master

    loop = asyncio.get_running_loop()

    full_name = f"{client_info.get('first_name', '')} {client_info.get('last_name', '')}".strip()

    raw_mobile = client_info.get("mobile", "").strip()
    formatted_mobile = raw_mobile
    if raw_mobile:
        digits = raw_mobile.replace(" ", "").replace("+61", "").replace("+", "")
        if digits.isdigit() and len(digits) == 10:
            if digits.startswith("0"):
                formatted_mobile = "+61" + digits[1:]
            else:
                formatted_mobile = "+61" + digits
        elif digits.isdigit() and len(digits) == 9:
            formatted_mobile = "0" + digits

    raw_bday = client_info.get("birthdate", "").strip()
    formatted_bday = ""
    if raw_bday:
        try:
            for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(raw_bday, fmt)
                    formatted_bday = dt.strftime("%d-%b-%Y")
                    break
                except Exception:
                    continue
        except Exception:
            formatted_bday = raw_bday

    client_data = {
        "from_name": full_name,
        "email_address": client_info.get("email", info.get("sender", "")),
        "mobile": formatted_mobile,
        "client_status": client_info.get("client_status", "New"),
        "estimator_or_site_manager": client_info.get("estimator_or_site_manager", ""),
        "birthdate": formatted_bday,
        "background_info": client_info.get(
            "background_info", f"Added from Ref #{ref_id}"
        ),
    }

    await loop.run_in_executor(None, add_new_client_to_master, client_data)
    db.delete_pending_approval(ref_id)

    return {
        "status": "success",
        "message": f"Client added: {full_name}",
        "client": client_info,
    }
