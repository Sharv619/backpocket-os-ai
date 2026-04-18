import logging
from fastapi import APIRouter, Request
import services.database as db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/twin-chat")
async def twin_chat(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        conversation_id = data.get("conversation_id", "")
        context_data = data.get("context", {})

        from services.memory import save_message_instant, create_conversation

        if not conversation_id:
            conversation_id = create_conversation()

        if message and message.startswith("/"):
            from routes.email import handle_slash_command

            response = await handle_slash_command(
                message, conversation_id, context_data
            )
            if response:
                save_message_instant(conversation_id, "user", message)
                save_message_instant(conversation_id, "assistant", response)
                return {
                    "response": response,
                    "conversation_id": conversation_id,
                    "is_command": True,
                }

        if message:
            save_message_instant(conversation_id, "user", message)

        session_context = ""
        chat_history = data.get("chat_history", [])
        try:
            from services.session_manager import (
                get_pending_actions,
                build_context_summary,
            )

            session_context = build_context_summary()
            pending_actions = get_pending_actions()
            if pending_actions:
                session_context += "\n\n### THINGS WE'VE AGREED TO DO ###\n"
                for a in pending_actions:
                    session_context += f"- [{a['status']}] {a['description']}\n"
        except Exception:
            pass

        recent_convo = ""
        if chat_history:
            recent_convo += "\n\n### OUR RECENT CONVERSATION ###\n"
            for msg in chat_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("message", msg.get("html", ""))
                recent_convo += f"{role}: {content[:100]}\n"

        try:
            from services.gemini import get_gemini_client

            client = get_gemini_client()
            if client:
                draft_context = ""
                if context_data.get("draft"):
                    draft_context = f"\n\nCURRENT EMAIL DRAFT:\n{context_data['draft']}\n\nSubject: {context_data.get('subject', 'N/A')}\nFrom: {context_data.get('sender', 'N/A')}"

                sender = context_data.get("sender", "")
                sender_instructions = ""
                if sender:
                    inst = db.get_sender_instruction(sender)
                    if inst:
                        sender_instructions = f"\n\nSPECIAL INSTRUCTIONS FOR THIS SENDER:\n{inst.get('instructions', '')}"

                db_context = _build_db_context(sender, context_data)

                prompt = _build_twin_prompt(
                    message, session_context, recent_convo,
                    db_context, draft_context, sender_instructions
                )

                response_obj = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                response = (
                    response_obj.text.strip()
                    if response_obj and response_obj.text
                    else f"I understand: '{message}'. What would you like help with?"
                )
            else:
                response = f"I understand: '{message}'. The AI is currently unavailable. How can I help?"
        except Exception as ai_err:
            logger.error(f"Twin AI error: {ai_err}", exc_info=True)
            response = f"I understand: '{message}'. How can I help? Discuss the draft, ask for improvements, or research topics."

        save_message_instant(conversation_id, "assistant", response)

        try:
            from services.session_manager import check_and_compact

            check_and_compact(conversation_id, threshold=20)
        except Exception:
            pass

        from services.memory import auto_title_if_needed

        new_title = auto_title_if_needed(conversation_id)

        return {
            "response": response,
            "conversation_id": conversation_id,
            "title": new_title,
        }
    except Exception as e:
        import traceback

        logger.error(f"Twin chat error: {e}\n{traceback.format_exc()}")
        return {"response": f"Error: {str(e)[:100]}", "error": str(e)}


def _build_db_context(sender: str, context_data: dict) -> str:
    db_context = ""
    pending_refs = [
        r for r in db.get_all_pending_refs() if not r.startswith("FIND-")
    ]
    if pending_refs:
        db_context += "\n\n### CURRENT PENDING APPROVALS ###\n"
        for ref in pending_refs:
            p = db.get_pending_approval(ref)
            if p:
                db_context += f"- Ref #{ref}: {p.get('subject', 'No subject')[:50]} (from {p.get('sender', 'Unknown')})\n"
    else:
        db_context += "\n\n### CURRENT PENDING APPROVALS ###\n- Your inbox is clear! No pending approvals."

    history = db.get_action_history(5)
    if history:
        db_context += "\n\n### RECENT ACTIVITY ###\n"
        for h in history:
            db_context += f"- {h['action']}: Ref #{h['ref_id']} ({h.get('created_at', '')})\n"

    try:
        from services.twin_brain import build_twin_context

        twin_context = build_twin_context(sender_email=sender)
        db_context += twin_context if twin_context else ""
    except Exception:
        pass

    learned = db.get_learned_patterns(
        sender_email=sender, subject=context_data.get("subject", "")
    )
    if learned:
        db_context += f"\n\n### LEARNED FROM PAST CORRECTIONS ###\nTwin learned from {len(learned)} similar situations:"
        for pat in learned[:3]:
            db_context += f"\n- [{pat.get('correction_type')}] {pat.get('subject', 'N/A')[:60]}: {pat.get('feedback', 'N/A')[:80]}"

    db_context += """
### EMAIL TRIAGE SYSTEM (TIER RULES) ###
TIER 1 - REPLY NEEDED: Important client emails requiring personalized response
TIER 2 - REVIEW NEEDED: Non-urgent but needs acknowledgment
TIER 3 - FYI ONLY: Info emails, no response needed
TIER 4 - ARCHIVE: Portal updates, digests, auto-generated
TIER 5 - LOW PRIORITY: Newsletters, promotions, spam-like

GOLDEN SENDERS (Always Tier 1):
- jco064690@gmail.com, trustdeed.com.au, gjcctax.au, cqstax.com
- almemmolos@gmail.com, johnwatts.com.au, david@vdmandthorn.com, che.tomenio1@gmail.com
"""
    return db_context


def _build_twin_prompt(
    message: str, session_context: str, recent_convo: str,
    db_context: str, draft_context: str, sender_instructions: str
) -> str:
    return f"""You are Steve's Twin - her AI assistant. She's chatting with you conversationally.

ABOUT YOU:
- You are Steve's Digital Twin, running on BackPocket OS
- You help Steve with email management, client communication, and business tasks
- You can discuss emails, drafts, pending approvals, and system status
- You CAN offer choices to Steve - use this format: "[CHOICES: Option 1 | Option 2 | Option 3]"
- When Steve agrees to something, acknowledge and offer to implement it: "Shall I implement this now?"

{session_context}
{recent_convo}

WHAT YOU KNOW:
- You have access to Steve's pending approvals list
- You have access to her action history
- You have access to sender-specific instructions
- You know about her email drafts when she's working on them
- You have memory of past sessions and agreed actions

SELF-CHECK RULES:
- Only state facts, don't hallucinate
- If unsure, say "I'm not sure, let me check with you"
- Don't make up dates, prices, or deadlines
- Always verify with user before assuming

FORMATTING RULES:
- Keep responses under 150 words
- Use headings with ## for major topics
- Use **bold** for key points
- Use bullet points for lists
- Make it easy to read, eyes-friendly
- Don't start every response with greeting - be natural

{db_context}
{draft_context}
{sender_instructions}

Steve says: "{message}"

Respond conversationally as the Twin. Be helpful, practical, and concise."""


@router.get("/api/twins")
async def get_twins():
    from services.twin_engine import list_twins

    return {"twins": list_twins()}


@router.post("/api/twins/chat")
async def twins_chat(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        twin_type = data.get("twin_type", "accountant")
        conversation_id = data.get("conversation_id")

        if not message:
            return {"error": "message is required"}, 400

        from services.twin_engine import twin_chat

        result = await twin_chat(twin_type, message, conversation_id)
        return result
    except Exception as e:
        logger.error(f"Twins chat error: {e}", exc_info=True)
        return {"response": f"Error: {str(e)[:100]}", "error": str(e)}


@router.post("/api/twins/ingest")
async def twins_ingest(request: Request):
    try:
        data = await request.json()
        twin_type = data.get("twin_type", "accountant")
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
