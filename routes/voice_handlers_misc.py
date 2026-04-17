"""
BackPocket OS — Voice Handlers: Documents, Marketing, Instructions, Chat
Handles all remaining per-screen intents.
"""

import logging
import httpx

from routes._voice_handlers import register_handler

logger = logging.getLogger(__name__)

BASE = "http://127.0.0.1:8000"


# ── Documents ────────────────────────────────────────────────────────────────

@register_handler("documents.list")
async def handle_documents_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/documents")
            if resp.status_code == 200:
                docs = resp.json() if isinstance(resp.json(), list) else resp.json().get("documents", [])
                analyzed = sum(1 for d in docs if d.get("analyzed") or d.get("status") == "analyzed")
                return {
                    "count": len(docs),
                    "analyzed": analyzed,
                    "_ui_action": {"navigate_to": "documents", "refresh_data": True},
                }
        except Exception as e:
            logger.warning(f"Documents list failed: {e}")
    return {"count": 0, "analyzed": 0}


@register_handler("documents.upload")
async def handle_documents_upload(params: dict, screen_context: str, metadata: dict | None) -> dict:
    return {
        "action": "open_camera",
        "speech": "Opening camera. Take a photo of the document.",
        "_ui_action": {"navigate_to": "documents", "show_modal": "camera"},
    }


@register_handler("documents.analyze")
async def handle_documents_analyze(params: dict, screen_context: str, metadata: dict | None) -> dict:
    doc_id = params.get("doc_id")
    if not doc_id:
        return {"error": "Which document should I analyze?"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{BASE}/api/documents/analyze/{doc_id}")
        if resp.status_code == 200:
            data = resp.json()
            return {
                "summary": data.get("summary", data.get("analysis", "Analysis complete.")),
                "_ui_action": {"navigate_to": "documents", "highlight_item": doc_id},
            }
    return {"error": "Failed to analyze document."}


@register_handler("documents.search")
async def handle_documents_search(params: dict, screen_context: str, metadata: dict | None) -> dict:
    query = params.get("query", "")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/documents")
            if resp.status_code == 200:
                docs = resp.json() if isinstance(resp.json(), list) else resp.json().get("documents", [])
                query_lower = query.lower()
                matches = [d for d in docs if query_lower in (d.get("name", "") + d.get("title", "")).lower()]
                return {
                    "count": len(matches),
                    "results": matches[:10],
                    "_ui_action": {"navigate_to": "documents"},
                }
        except Exception as e:
            logger.warning(f"Documents search failed: {e}")
    return {"count": 0, "results": []}


# ── Marketing ────────────────────────────────────────────────────────────────

@register_handler("marketing.create_post")
async def handle_marketing_post(params: dict, screen_context: str, metadata: dict | None) -> dict:
    job_desc = params.get("job_description", "")
    suburb = params.get("suburb", "")

    if not job_desc or not suburb:
        return {"error": "Need a job description and suburb for the post."}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{BASE}/api/marketing/gbp-post",
            json={"job_description": job_desc, "suburb": suburb},
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "post": data.get("post", data.get("content", "")),
                "_ui_action": {"navigate_to": "marketing", "refresh_data": True},
            }
    return {"error": "Failed to create post."}


@register_handler("marketing.insights")
async def handle_marketing_insights(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/marketing/insights")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "search_growth": data.get("growth", ""),
                    "insights": data,
                    "_ui_action": {"navigate_to": "marketing"},
                }
        except Exception as e:
            logger.warning(f"Marketing insights failed: {e}")
    return {"search_growth": "unavailable"}


@register_handler("marketing.activity")
async def handle_marketing_activity(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/marketing/activity")
            if resp.status_code == 200:
                data = resp.json()
                activity = data.get("activity", [])
                return {
                    "count": len(activity),
                    "activity": activity[:10],
                    "_ui_action": {"navigate_to": "marketing"},
                }
        except Exception as e:
            logger.warning(f"Marketing activity failed: {e}")
    return {"count": 0, "activity": []}


# ── Instructions ─────────────────────────────────────────────────────────────

@register_handler("instructions.list")
async def handle_instructions_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/instructions")
            if resp.status_code == 200:
                instructions = resp.json() if isinstance(resp.json(), list) else resp.json().get("instructions", [])
                return {
                    "count": len(instructions),
                    "_ui_action": {"navigate_to": "instructions", "refresh_data": True},
                }
        except Exception as e:
            logger.warning(f"Instructions list failed: {e}")
    return {"count": 0}


@register_handler("instructions.add")
async def handle_instructions_add(params: dict, screen_context: str, metadata: dict | None) -> dict:
    text = params.get("text", "")
    category = params.get("category", "general")

    if not text:
        return {"error": "What instruction should I add?"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{BASE}/api/instructions",
            json={"instruction_text": text, "category": category, "is_active": 1},
        )
        if resp.status_code == 200:
            return {
                "text": text,
                "category": category,
                "_ui_action": {"navigate_to": "instructions", "refresh_data": True},
            }
    return {"error": "Failed to save instruction."}


@register_handler("instructions.delete")
async def handle_instructions_delete(params: dict, screen_context: str, metadata: dict | None) -> dict:
    instruction_id = params.get("id")
    keyword = params.get("keyword", "")

    if not instruction_id and keyword:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE}/api/instructions")
            if resp.status_code == 200:
                instructions = resp.json() if isinstance(resp.json(), list) else resp.json().get("instructions", [])
                kw_lower = keyword.lower()
                for inst in instructions:
                    if kw_lower in (inst.get("instruction_text", "") + inst.get("text", "")).lower():
                        instruction_id = inst.get("id")
                        break

    if not instruction_id:
        return {"error": "Couldn't find that instruction."}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.delete(f"{BASE}/api/instructions/{instruction_id}")
        if resp.status_code == 200:
            return {
                "deleted_id": instruction_id,
                "_ui_action": {"navigate_to": "instructions", "refresh_data": True},
            }
    return {"error": "Failed to delete instruction."}


# ── Chat (fallback) ─────────────────────────────────────────────────────────

@register_handler("chat.ask")
async def handle_chat_ask(params: dict, screen_context: str, metadata: dict | None) -> dict:
    message = params.get("message", params.get("transcript", ""))
    if not message:
        return {"response": "What would you like to know?"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{BASE}/api/mobile/chat",
            json={"message": message},
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "response": data.get("response", data.get("message", "")),
                "_ui_action": {"navigate_to": "chat"},
            }
    return {"response": "Couldn't get a response right now."}


@register_handler("chat.clear")
async def handle_chat_clear(params: dict, screen_context: str, metadata: dict | None) -> dict:
    return {
        "cleared": True,
        "_ui_action": {"navigate_to": "chat", "clear_chat": True},
    }
