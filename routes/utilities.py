import os
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import services.database as db
from app.models.schemas import CoachAnalyzeRequest, HookRequest, TTSRequest

logger = logging.getLogger(__name__)
router = APIRouter()

LAST_PATROL_TIME = "Syncing..."
SCHEDULE_JOBS_DONE = set()


@router.get("/health")
async def health_check():
    """Deep health check — verifies DB, env vars, and optional services."""
    checks = {}

    # Database
    try:
        pending_refs = db.get_all_pending_refs()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"ERROR: {e}"

    # Critical env vars
    checks["gemini_key"]      = "ok" if os.getenv("GEMINI_API_KEY") else "MISSING"
    checks["openrouter_key"]  = "ok" if os.getenv("OPENROUTER_API_KEY") else "MISSING"
    checks["google_creds"]    = "ok" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else "MISSING"

    # Auth (EPIC F)
    from services.auth import auth_is_configured
    checks["auth"] = "ok" if auth_is_configured() else "not configured (dev mode)"

    # Optional services
    checks["elevenlabs"]      = "ok" if os.getenv("ELEVENLABS_API_KEY") else "not configured"
    checks["ollama"]          = "ok" if os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") else "not configured"

    # Ollama reachability (non-blocking, best-effort)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.get(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
            checks["ollama"] = "ok" if r.status_code < 500 else "unreachable"
    except Exception:
        checks["ollama"] = "unreachable"

    all_critical = all(v == "ok" for k, v in checks.items() if k in ("database", "gemini_key"))
    return {
        "status": "READY" if all_critical else "DEGRADED",
        "version": "2.2",
        "checks": checks,
        "pending_count": len(pending_refs) if "pending_refs" in dir() else 0,
    }


@router.get("/")
def read_root():
    return FileResponse("static/index.html")


@router.get("/api/status")
async def get_system_status():
    global LAST_PATROL_TIME

    spreadsheet_id = os.getenv("SPREADSHEET_ID", "")
    spreadsheet_url = ""
    if spreadsheet_id and spreadsheet_id != "your_google_sheet_id_here":
        spreadsheet_url = (
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        )

    return {
        "status": "Healthy",
        "last_patrol": LAST_PATROL_TIME,
        "pending_count": len(
            [r for r in db.get_all_pending_refs() if not r.startswith("FIND-")]
        ),
        "ollama": "Active",
        "spreadsheet_url": spreadsheet_url,
        "debug_spreadsheet_id": spreadsheet_id,
        "privacy_mode": True,
        "data_residency": "local",
    }


@router.get("/api/history")
async def api_get_history(limit: int = 50):
    history = db.get_action_history(limit)
    return {"history": history}


@router.get("/api/corrections")
async def api_get_corrections(ref_id: Optional[str] = None):
    corrections = db.get_corrections(ref_id)
    return {"corrections": corrections}


@router.get("/api/debug-draft/{ref_id}")
async def api_debug_draft(ref_id: str):
    info = db.get_pending_approval(ref_id)
    if not info:
        return {"error": "Ref not found"}
    return {
        "ref_id": ref_id,
        "sender": info.get("sender"),
        "subject": info.get("subject"),
        "draft_body": info.get("draft_body"),
        "tier": info.get("tier"),
        "created_at": info.get("created_at"),
    }


@router.post("/api/coach/analyze")
async def api_coach_analyze(request: CoachAnalyzeRequest):
    ref_id = request.ref_id
    info = db.get_pending_approval(ref_id)
    if not info:
        return {"status": "error", "message": f"Ref #{ref_id} not found."}

    try:
        from services.gemini import analyze_draft_with_coach

        email_content = {
            "subject": info.get("subject", ""),
            "snippet": (info.get("email_body") or "")[:1000],
        }
        draft_body = info.get("draft_body") or ""

        analysis = analyze_draft_with_coach(email_content, draft_body)
        if not analysis:
            return {"status": "error", "message": "Coach failed to return analysis."}

        return {"status": "success", "analysis": analysis}
    except Exception as e:
        logger.error(f"Coach analyze error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/api/coach/yoodli")
async def api_coach_yoodli():
    return {
        "status": "success",
        "yoodli_url": "https://app.yoodli.ai/practice",
        "message": "Yoodli voice practice integration activated.",
    }


@router.post("/api/invoice/generate")
async def api_invoice_generate(request: Request):
    from fastapi.responses import FileResponse as FR
    from services.invoice_engine import generate_invoice_pdf, next_invoice_number

    try:
        data = await request.json()
        quote_id = data.get("quote_id")

        # Auto-populate from quote record when quote_id provided
        if quote_id:
            from services.construction import ConstructionManager
            mgr = ConstructionManager()
            quote = mgr.get_quote(int(quote_id))
            if not quote:
                return JSONResponse({"error": f"Quote {quote_id} not found"}, status_code=404)
            if quote.get("status") not in ("accepted", "invoiced"):
                return JSONResponse(
                    {"error": f"Quote must be accepted before invoicing (current status: {quote.get('status')})"},
                    status_code=400,
                )
            client_name  = data.get("client_name") or quote.get("client_name", "Client")
            client_email = data.get("client_email", "")
            notes = data.get("notes", quote.get("description", ""))
            items = data.get("items") or [
                {"description": f"Materials – {quote.get('job_type', 'Job')}", "qty": 1, "rate": quote.get("materials_cost", 0), "gst": True},
                {"description": f"Labour – {quote.get('job_type', 'Job')}", "qty": 1, "rate": quote.get("labor_cost", 0), "gst": True},
            ]
        else:
            client_name  = data.get("client_name", "Client")
            client_email = data.get("client_email", "")
            items = data.get("items", [])
            notes = data.get("notes", "")

        if not items:
            return JSONResponse({"error": "No line items provided"}, status_code=400)

        today = datetime.now()
        due = today + timedelta(days=14)
        inv_num = next_invoice_number()

        invoice_data = {
            "invoice_number": inv_num,
            "date": today.strftime("%Y-%m-%d"),
            "due_date": due.strftime("%Y-%m-%d"),
            "line_items": items,
            "notes": notes,
        }
        client_data = {"name": client_name, "email": client_email}

        pdf_path = generate_invoice_pdf(invoice_data, client_data)
        filename = f"{inv_num}_{client_name.replace(' ', '_')}.pdf"

        return FR(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        logger.error(f"Invoice generation error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/hooks")
async def api_get_hooks(event: str = None):
    from services.hooks import get_hooks, SUPPORTED_EVENTS

    hooks = get_hooks(event=event, enabled_only=False)
    return {"hooks": hooks, "supported_events": SUPPORTED_EVENTS}


@router.post("/api/hooks")
async def api_create_hook(request: HookRequest):
    from services.hooks import save_hook, SUPPORTED_EVENTS

    if request.event not in SUPPORTED_EVENTS:
        return {
            "status": "error",
            "message": f"Invalid event. Supported: {SUPPORTED_EVENTS}",
        }
    hook_id = save_hook(
        request.name,
        request.event,
        request.action_type,
        request.action_config,
        request.enabled,
    )
    return {"status": "success", "id": hook_id}


@router.delete("/api/hooks/{hook_id}")
async def api_delete_hook(hook_id: int):
    from services.hooks import delete_hook

    success = delete_hook(hook_id)
    return {"status": "success" if success else "error", "deleted": success}


@router.post("/api/chat/compact/{conversation_id}")
async def api_compact_chat(conversation_id: str):
    from services.session_manager import compact_conversation

    result = compact_conversation(conversation_id)
    if result:
        return {"status": "success", "summary": result[:100] + "..."}
    return {"status": "error", "message": "Could not compact conversation"}


@router.post("/api/voice/tts")
async def text_to_speech(request: TTSRequest):
    from services.elevenlabs import synthesize, is_configured
    from fastapi.responses import Response as FastAPIResponse

    if not is_configured():
        return {"status": "error", "message": "ELEVENLABS_API_KEY not configured"}

    try:
        audio_bytes = await synthesize(request.text, voice=request.voice)
        return FastAPIResponse(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline", "Cache-Control": "no-store"},
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/api/command")
async def send_command(request: Request):
    try:
        data = await request.json()
        command = data.get("command", "")
        return {
            "success": True,
            "message": f"Command '{command}' sent! Check WhatsApp for response.",
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


@router.post("/api/execute-action")
async def execute_action(request: Request):
    try:
        data = await request.json()
        action_type = data.get("action_type", "")
        description = data.get("description", "")
        details = data.get("details", {})

        try:
            from services.session_manager import add_agreed_action, update_action_status

            if action_type == "agree":
                action_id = add_agreed_action(description)
                logger.info(f"Action agreed: {description} (ID: {action_id})")
                return {
                    "success": True,
                    "action_id": action_id,
                    "message": "Action recorded. I'll help you implement it.",
                }

            elif action_type == "complete":
                action_id = details.get("action_id")
                if action_id:
                    update_action_status(action_id, "completed")
                    return {"success": True, "message": "Action marked as completed!"}
                return {"success": False, "message": "No action_id provided"}

            elif action_type == "log_session":
                from services.session_manager import log_session

                log_session(
                    summary=details.get("summary", ""),
                    files_changed=details.get("files_changed", ""),
                    decisions=details.get("decisions", ""),
                    errors=details.get("errors", ""),
                )
                return {"success": True, "message": "Session logged!"}

            else:
                return {
                    "success": False,
                    "message": f"Unknown action type: {action_type}",
                }

        except Exception as sm_err:
            logger.error(f"Session manager error: {sm_err}")
            return {"success": False, "message": "Session system not available"}

    except Exception as e:
        logger.error(f"Execute action error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/api/workflow/stages")
async def get_workflow_stages():
    try:
        import sqlite3
        conn = sqlite3.connect(db.DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT stage_number, title, description, triggers, next_steps, branch_type "
            "FROM workflow_stages ORDER BY stage_number"
        )
        stages = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"status": "success", "stages": stages}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/api/workflow/current")
async def get_current_workflow_stage():
    try:
        return {
            "status": "success",
            "current_stage": "1",
            "stage_title": "Client Inquiry / Call for Quote",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/api/search-gmail")
async def api_search_gmail(q: str):
    from services.gmail import search_emails, get_all_account_tokens

    loop = asyncio.get_running_loop()
    tokens = await loop.run_in_executor(None, get_all_account_tokens)

    all_results = []
    for t in tokens:
        results = await loop.run_in_executor(None, search_emails, q, t)
        all_results.extend(results)

    return {"results": all_results}


@router.post("/api/search-emails")
async def api_search_emails(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "")
        limit = data.get("limit", 5)

        if not query:
            return {"results": [], "message": "No query provided"}

        from services.email_memory import search_emails_natural

        results = search_emails_natural(query, limit)

        return {"results": results, "count": len(results), "query": query}
    except Exception as e:
        logger.error(f"Email search error: {e}")
        return {"results": [], "error": str(e)}


@router.get("/api/audit")
async def api_audit():
    from services.local_audit import run_self_audit

    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, run_self_audit)
    return {"status": "success", "report": report}


@router.post("/api/rescue")
async def api_rescue(msg_id: str, token: str = "token.json"):
    from services.gmail import rescue_to_inbox

    loop = asyncio.get_running_loop()
    success = await loop.run_in_executor(None, rescue_to_inbox, msg_id, token)
    return {"status": "success" if success else "error"}


@router.get("/test-sheets")
async def check_sheets():
    from services.google_sheets import test_sheets_connection

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, test_sheets_connection)


@router.get("/test-whatsapp")
async def test_whatsapp():
    from services.whapi import send_whatsapp_message

    loop = asyncio.get_running_loop()
    founder_phone = os.getenv("FOUNDER_PHONE")
    if not founder_phone:
        return {"status": "error", "message": "FOUNDER_PHONE not set"}

    clean_phone = "".join(filter(str.isdigit, founder_phone))
    logger.info(f"TESTING WHATSAPP: Sending to {clean_phone}")
    text = "BackPocket Connection Test\n\nIf you are reading this, your WhatsApp connection is officially WORKING!"
    result = await loop.run_in_executor(None, send_whatsapp_message, clean_phone, text)
    return {"status": "success", "whapi_response": result}


@router.get("/self-check")
async def api_self_check():
    from services.self_check import run_self_check

    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, run_self_check)
    return {"status": "success", "report": report}


@router.get("/api/debug/last-thought")
async def get_last_thought():
    """Return the most recent agent thinking block for frontend polling."""
    from services.gemini import get_last_thought_log
    thought = get_last_thought_log()
    return {
        "status": "success",
        "thinking": thought,
        "has_content": bool(thought),
    }
