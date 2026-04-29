import logging
import os
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/twins")
async def get_twins():
    """List the three specialized AI twins."""
    from services.twin_engine import list_twins
    return {"twins": list_twins()}


@router.post("/api/twins/chat")
async def twins_chat(request: Request):
    """Twin chat endpoint using the older mobile-chat style prompt path."""
    try:
        data = await request.json()
        message = data.get("message", "")
        twin_type = data.get("twin_type", "estimator")
        conversation_id = data.get("conversation_id")

        if not message:
            return {"error": "message is required"}, 400

        from services.memory import (
            auto_title_if_needed,
            create_conversation,
            get_conversation_messages,
            save_message_instant,
        )
        from services.twin_brain import build_twin_context

        if not conversation_id:
            conversation_id = create_conversation(source="twin")

        save_message_instant(conversation_id, "user", message)
        prior_messages = get_conversation_messages(conversation_id, limit=12)
        history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in prior_messages[:-1]
            if msg.get("role") in {"user", "assistant"} and msg.get("content")
        ]

        context = ""
        try:
            context = build_twin_context()
        except Exception:
            pass

        _owner = os.getenv("BP_OWNER_NAME", "the founder")
        _sector = os.getenv("BP_BUSINESS_TYPE", "business")
        twin_hint = {
            "estimator": "Focus on quoting, pricing, scope, margin, and commercial judgement.",
            "site_manager": "Focus on delivery, sequencing, materials, risks, defects, and site operations.",
            "admin": "Focus on inbox, follow-ups, scheduling, and practical business admin.",
        }.get(twin_type, "")

        system_prompt = (
            f"You are BackPocket OS for {_owner}. "
            f"You help run a {_sector} in a direct, Australian-practical way. "
            "Do not sound like a generic AI assistant. "
            "No hype, no filler, no 'as an AI'. "
            "Keep replies human, switched-on, and useful.\n\n"
            f"{twin_hint}\n\n"
            f"{context}"
        )

        reply = None

        if os.getenv("FORCE_OLLAMA_DEMO") == "1":
            import ollama

            response = ollama.chat(
                model="llama3.2:1b",
                messages=[{"role": "system", "content": system_prompt}] + history[-8:] + [
                    {"role": "user", "content": message}
                ],
            )
            reply = response["message"]["content"]
        else:
            from services.gemini import get_gemini_client
            from google.genai import types as genai_types

            client = get_gemini_client()
            if not client:
                reply = "AI not available — check GEMINI_API_KEY."
            else:
                conversation_text = "\n".join(
                    f"{'User' if msg['role'] == 'user' else 'BackPocket'}: {msg['content']}"
                    for msg in history[-8:]
                )
                prompt = message
                if conversation_text:
                    prompt = (
                        "Continue this existing conversation naturally.\n\n"
                        f"{conversation_text}\n"
                        f"User: {message}"
                    )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_prompt
                    ),
                )
                reply = response.text or "Sorry, no response generated."

        save_message_instant(conversation_id, "assistant", reply)
        auto_title_if_needed(conversation_id)

        return {
            "response": reply,
            "twin_type": twin_type,
            "conversation_id": conversation_id,
        }
    except Exception as e:
        logger.error(f"Twins chat error: {e}", exc_info=True)
        return {"response": f"Error: {str(e)[:100]}", "error": str(e)}


@router.post("/api/twins/ingest")
async def twins_ingest(request: Request):
    try:
        data = await request.json()
        twin_type = data.get("twin_type", "estimator")
        doc_id = data.get("doc_id", str(__import__("uuid").uuid4()))
        text = data.get("text", "")
        metadata = data.get("metadata", {})

        if not text:
            return {"error": "text is required"}, 400

        from services.twin_engine import ingest_document

        ok = ingest_document(twin_type, doc_id, text, metadata)
        return {
            "status": "ingested" if ok else "chromadb_unavailable",
            "doc_id": doc_id,
        }
    except Exception as e:
        logger.error(f"Twins ingest error: {e}", exc_info=True)
        return {"error": str(e)}


@router.get("/api/conversations")
async def get_conversations():
    try:
        from services.memory import get_all_conversations

        conversations = get_all_conversations(limit=30)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        return {"conversations": [], "error": str(e)}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation_messages(conversation_id: str):
    try:
        from services.memory import get_conversation_messages

        messages = get_conversation_messages(conversation_id, limit=100)
        return {"conversation_id": conversation_id, "messages": messages}
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        return {"conversation_id": conversation_id, "messages": [], "error": str(e)}


@router.get("/api/conversations/{conversation_id}/recent")
async def get_recent(conversation_id: str, limit: int = 10):
    try:
        from services.memory import get_conversation_messages

        messages = get_conversation_messages(conversation_id, limit=limit)
        return {"messages": messages}
    except Exception as e:
        return {"messages": [], "error": str(e)}


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    try:
        import sqlite3
        from services.memory import DB_PATH

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM chat_messages WHERE conversation_id = ?", (conversation_id,)
        )
        cur.execute("DELETE FROM chat_conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/opencode/conversations")
async def get_opencode_conversations():
    try:
        from services.memory import get_opencode_conversations

        conversations = get_opencode_conversations(limit=50)
        return {"conversations": conversations}
    except Exception as e:
        return {"conversations": [], "error": str(e)}


@router.post("/api/opencode-chat")
async def opencode_chat(request: Request):
    try:
        from services.memory import save_message_instant, create_conversation

        data = await request.json()
        message = data.get("message", "")
        conversation_id = data.get("conversation_id", "")
        role = data.get("role", "user")

        if not conversation_id:
            conversation_id = create_conversation(source="opencode")
            logger.info(f"Created new OpenCode conversation: {conversation_id}")

        if message:
            msg_id = save_message_instant(conversation_id, role, message)
            logger.debug(f"Saved message {msg_id} to conversation {conversation_id}")

        from services.memory import auto_title_if_needed

        new_title = auto_title_if_needed(conversation_id)

        return {"conversation_id": conversation_id, "saved": True, "title": new_title}
    except Exception as e:
        logger.error(f"OpenCode chat save error: {e}")
        return {"error": str(e), "saved": False}


@router.get("/api/search")
async def search_chats(q: str = "", source: str = None):
    try:
        from services.memory import search_messages

        results = search_messages(q, source=source, limit=30)
        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"results": [], "error": str(e)}


@router.get("/api/conversations/by-source/{source}")
async def get_conversations_by_source(source: str):
    try:
        from services.memory import get_all_conversations

        conversations = get_all_conversations(limit=50, source=source)
        return {"source": source, "conversations": conversations}
    except Exception as e:
        return {"source": source, "conversations": [], "error": str(e)}


@router.put("/api/conversations/{conversation_id}/title")
async def rename_conversation(conversation_id: str, request: Request):
    try:
        from services.memory import update_conversation_title

        data = await request.json()
        new_title = data.get("title", "").strip()

        if not new_title:
            return {"success": False, "error": "Title cannot be empty"}

        if len(new_title) > 100:
            return {"success": False, "error": "Title too long (max 100 chars)"}

        update_conversation_title(conversation_id, new_title)
        logger.info(f"Renamed conversation {conversation_id[:20]} to: {new_title}")

        return {"success": True, "title": new_title}
    except Exception as e:
        logger.error(f"Rename conversation error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/api/conversations/{conversation_id}/regenerate-title")
async def regenerate_conversation_title(conversation_id: str):
    try:
        from services.memory import generate_conversation_title

        new_title = generate_conversation_title(conversation_id)

        if new_title:
            logger.info(f"Regenerated title for {conversation_id[:20]}: {new_title}")
            return {"success": True, "title": new_title}
        else:
            return {"success": False, "error": "Could not generate title"}
    except Exception as e:
        logger.error(f"Regenerate title error: {e}")
        return {"success": False, "error": str(e)}
