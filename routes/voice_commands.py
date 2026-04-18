"""
BackPocket OS — Voice Command Router
Central router: receives transcript + context, classifies intent, dispatches action.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.intent_classifier import classify_intent
from services.voice_session import (
    SessionState,
    VoiceSession,
    session_manager,
    CONFIRM_REQUIRED,
    STRONG_CONFIRM,
    PARAM_ORDER,
)
from services.entity_resolver import resolve_entity, get_available_entities
from services.voice_response import (
    generate_response,
    generate_confirmation_prompt,
    generate_error_response,
    generate_disambiguation,
    generate_collecting_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice-commands"])

SCREEN_NAMES = {
    "dashboard", "inbox", "chat", "documents",
    "marketing", "instructions", "construction", "settings",
}

SCREEN_TAB_MAP = {
    "dashboard": 0, "inbox": 1, "chat": 2, "documents": 3,
    "marketing": 4, "instructions": 5, "construction": 6, "settings": 7,
}

YES_WORDS = {"yes", "yeah", "yep", "do it", "go for it", "send it", "save it", "confirmed", "send them all", "she'll be right", "give it the tick"}
NO_WORDS = {"no", "nah", "cancel", "hold on", "wait", "stop", "never mind"}


# ── Request / Response Models ────────────────────────────────────────────────

class VoiceCommandRequest(BaseModel):
    transcript: str
    screen_context: str = "dashboard"
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


class VoiceConfirmRequest(BaseModel):
    session_id: str
    response: str


class VoiceCommandResponse(BaseModel):
    intent: Optional[str] = None
    confidence: float = 0.0
    action: str = "display"
    result: dict = {}
    speech_response: str = ""
    ui_action: dict = {}
    needs_confirmation: bool = False
    follow_up_prompt: Optional[str] = None
    session_state: Optional[dict] = None


# ── Main Command Endpoint ────────────────────────────────────────────────────

@router.post("/command", response_model=VoiceCommandResponse)
async def voice_command(req: VoiceCommandRequest) -> VoiceCommandResponse:
    if not req.transcript or not req.transcript.strip():
        return VoiceCommandResponse(
            speech_response=generate_error_response("transcription_failed"),
            action="clarify",
        )

    session = session_manager.get_or_create(req.session_id)
    transcript = req.transcript.strip()

    if session.state == SessionState.CONFIRMING:
        return await _handle_confirmation_response(session, transcript)

    if session.state == SessionState.COLLECTING:
        return await _handle_collecting_response(session, transcript, req.screen_context)

    available = get_available_entities(req.screen_context)
    classification = await classify_intent(
        transcript=transcript,
        screen_context=req.screen_context,
        session_state=session.to_dict() if session.state != SessionState.IDLE else None,
        available_entities=available,
    )

    intent = classification.get("intent", "chat.ask")
    confidence = classification.get("confidence", 0.0)
    entities = classification.get("entities", {})

    if confidence < 0.4:
        return VoiceCommandResponse(
            intent=intent,
            confidence=confidence,
            action="clarify",
            speech_response=generate_error_response("low_confidence"),
            session_state=session.to_dict(),
        )

    if confidence < 0.7 and intent != "chat.ask":
        return VoiceCommandResponse(
            intent=intent,
            confidence=confidence,
            action="clarify",
            speech_response=f"Did you mean to {intent.replace('.', ' ')}? Say yes or try again.",
            session_state=session.to_dict(),
        )

    return await _dispatch_intent(session, intent, entities, req.screen_context, req.metadata)


async def _dispatch_intent(
    session: VoiceSession,
    intent: str,
    entities: dict,
    screen_context: str,
    metadata: dict | None = None,
) -> VoiceCommandResponse:
    session.intent = intent
    session.touch()

    if intent.startswith("navigate.") or intent == "dashboard.navigate":
        return _handle_navigate(session, entities)

    if intent == "meta.help":
        return VoiceCommandResponse(
            intent=intent, confidence=1.0, action="display",
            speech_response=generate_response("meta.help", {}),
            session_state=session.to_dict(),
        )

    if intent == "meta.cancel":
        session.reset()
        return VoiceCommandResponse(
            intent=intent, confidence=1.0, action="execute",
            speech_response=generate_response("meta.cancel", {}),
            session_state=session.to_dict(),
        )

    if intent == "meta.undo":
        return await _handle_undo(session)

    if intent in PARAM_ORDER:
        session.start_collecting(intent, entities)
        if session.state == SessionState.CONFIRMING:
            prompt = generate_confirmation_prompt(intent, session.collected_params, intent in STRONG_CONFIRM)
            return VoiceCommandResponse(
                intent=intent, confidence=1.0, action="confirm",
                result=session.collected_params,
                speech_response=prompt,
                needs_confirmation=True,
                session_state=session.to_dict(),
            )
        return VoiceCommandResponse(
            intent=intent, confidence=1.0, action="collect",
            result=session.collected_params,
            speech_response=generate_collecting_response(intent, session.next_question or "", session.collected_params),
            follow_up_prompt=session.next_question,
            session_state=session.to_dict(),
        )

    # Intents not in PARAM_ORDER but still requiring confirmation (e.g. inbox.approve)
    if intent in CONFIRM_REQUIRED and session.state != SessionState.CONFIRMING:
        session.intent = intent
        session.state = SessionState.CONFIRMING
        session.pending_action = {"intent": intent, "params": entities}
        prompt = generate_confirmation_prompt(intent, entities, intent in STRONG_CONFIRM)
        return VoiceCommandResponse(
            intent=intent, confidence=1.0, action="confirm",
            result=entities,
            speech_response=prompt,
            needs_confirmation=True,
            session_state=session.to_dict(),
        )

    return await _execute_intent(session, intent, entities, screen_context, metadata)


async def _handle_confirmation_response(session: VoiceSession, transcript: str) -> VoiceCommandResponse:
    lower = transcript.lower().strip()

    if any(w in lower for w in YES_WORDS):
        action_data = session.confirm()
        return await _execute_intent(
            session,
            action_data["intent"],
            action_data["params"],
            "construction",
        )

    if any(w in lower for w in NO_WORDS):
        session.cancel()
        session.reset()
        return VoiceCommandResponse(
            intent=session.intent, confidence=1.0, action="execute",
            speech_response="Cancelled.",
            session_state=session.to_dict(),
        )

    return VoiceCommandResponse(
        intent=session.intent, confidence=1.0, action="confirm",
        speech_response="Sorry, didn't catch that. Say 'yes' to confirm or 'no' to cancel.",
        needs_confirmation=True,
        session_state=session.to_dict(),
    )


async def _handle_collecting_response(session: VoiceSession, transcript: str, screen_context: str) -> VoiceCommandResponse:
    lower = transcript.lower().strip()
    if any(w in lower for w in NO_WORDS):
        session.cancel()
        session.reset()
        return VoiceCommandResponse(
            intent=session.intent, confidence=1.0, action="execute",
            speech_response="Cancelled.",
            session_state=session.to_dict(),
        )

    value = _parse_param_value(transcript, session.missing_params[0] if session.missing_params else "")

    if session.missing_params and session.missing_params[0] in ("lead_id", "quote_id"):
        resolved = resolve_entity(
            "lead" if "lead" in session.missing_params[0] else "quote",
            transcript,
            session.last_entity,
        )
        if resolved["match"] == "multiple":
            return VoiceCommandResponse(
                intent=session.intent, confidence=1.0, action="clarify",
                speech_response=generate_disambiguation(
                    "lead" if "lead" in session.missing_params[0] else "quote",
                    resolved["candidates"],
                ),
                session_state=session.to_dict(),
            )
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            value = resolved["entity"]["id"]
            session.last_entity = resolved["entity"]

    next_q = session.collect_next_param(value)

    if session.state == SessionState.CONFIRMING:
        prompt = generate_confirmation_prompt(
            session.intent or "",
            session.collected_params,
            (session.intent or "") in STRONG_CONFIRM,
        )
        return VoiceCommandResponse(
            intent=session.intent, confidence=1.0, action="confirm",
            result=session.collected_params,
            speech_response=prompt,
            needs_confirmation=True,
            session_state=session.to_dict(),
        )

    return VoiceCommandResponse(
        intent=session.intent, confidence=1.0, action="collect",
        result=session.collected_params,
        speech_response=generate_collecting_response(session.intent or "", next_q or "", session.collected_params),
        follow_up_prompt=next_q,
        session_state=session.to_dict(),
    )


def _parse_param_value(transcript: str, param_name: str):
    """Parse a raw transcript value into the appropriate type for a parameter."""
    clean = transcript.strip()

    if param_name in ("estimated_budget", "materials_cost", "labor_cost", "amount", "markup_percent"):
        import re
        numbers = re.findall(r'[\d,]+\.?\d*', clean.replace("$", "").replace("grand", "000").replace("k", "000"))
        if numbers:
            try:
                return float(numbers[0].replace(",", ""))
            except ValueError:
                pass

    if param_name in ("lead_id", "quote_id"):
        import re
        numbers = re.findall(r'\d+', clean)
        if numbers:
            return int(numbers[0])

    return clean


def _handle_navigate(session: VoiceSession, entities: dict) -> VoiceCommandResponse:
    target = entities.get("target", entities.get("target_screen", "")).lower()
    for screen in SCREEN_NAMES:
        if screen in target:
            session.reset()
            return VoiceCommandResponse(
                intent="navigate.screen", confidence=1.0, action="navigate",
                speech_response="",
                ui_action={
                    "navigate_to": screen,
                    "tab_index": SCREEN_TAB_MAP.get(screen, 0),
                },
                session_state=session.to_dict(),
            )
    return VoiceCommandResponse(
        intent="navigate.screen", confidence=0.5, action="clarify",
        speech_response=f"Which screen? Dashboard, inbox, chat, documents, marketing, instructions, construction, or settings?",
        session_state=session.to_dict(),
    )


async def _handle_undo(session: VoiceSession) -> VoiceCommandResponse:
    entry = session.pop_undo()
    if not entry:
        return VoiceCommandResponse(
            intent="meta.undo", confidence=1.0, action="display",
            speech_response="Nothing to undo.",
            session_state=session.to_dict(),
        )
    return VoiceCommandResponse(
        intent="meta.undo", confidence=1.0, action="execute",
        result=entry,
        speech_response=generate_response("meta.undo", entry),
        session_state=session.to_dict(),
    )


async def _execute_intent(
    session: VoiceSession,
    intent: str,
    params: dict,
    screen_context: str,
    metadata: dict | None = None,
) -> VoiceCommandResponse:
    """Execute an intent by calling the appropriate handler. Handlers are registered in chunks 5-14."""
    from routes._voice_handlers import execute_handler

    try:
        result = await execute_handler(intent, params, screen_context, metadata)
        speech = generate_response(intent, result)
        ui_action = result.pop("_ui_action", {})

        if result.get("_entity"):
            session.last_entity = result.pop("_entity")

        session.complete(result)
        session.reset()

        return VoiceCommandResponse(
            intent=intent, confidence=1.0, action="execute",
            result=result, speech_response=speech,
            ui_action=ui_action,
            session_state=session.to_dict(),
        )
    except Exception as e:
        logger.error(f"Intent execution error ({intent}): {e}")
        session.reset()
        return VoiceCommandResponse(
            intent=intent, confidence=1.0, action="display",
            speech_response=generate_error_response("server_error", str(e)),
            session_state=session.to_dict(),
        )


# ── Session Management Endpoints ─────────────────────────────────────────────

@router.post("/session")
async def create_session() -> dict:
    session = session_manager.get_or_create()
    return session.to_dict()


@router.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    session_manager.delete(session_id)
    return {"status": "deleted", "session_id": session_id}


@router.post("/confirm")
async def confirm_action(req: VoiceConfirmRequest) -> VoiceCommandResponse:
    session = session_manager.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await _handle_confirmation_response(session, req.response)


@router.get("/intents")
async def get_intents(screen: str = "dashboard") -> dict:
    """Return available intents for the given screen context."""
    from services.intent_classifier import INTENT_TAXONOMY
    screen_intents = []
    for line in INTENT_TAXONOMY.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("—")
        if len(parts) == 2:
            intent_name = parts[0].strip()
            examples = parts[1].strip().strip('"')
            if intent_name.startswith(screen) or intent_name.startswith("navigate.") or intent_name.startswith("meta.") or intent_name.startswith("cross."):
                screen_intents.append({"intent": intent_name, "examples": examples})
    return {"screen": screen, "intents": screen_intents}
