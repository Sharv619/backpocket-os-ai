"""
BackPocket OS — Voice Session State Machine
Multi-turn conversation tracking for voice commands.

States: IDLE → CLASSIFYING → COLLECTING → CONFIRMING → EXECUTING → COMPLETE
"""

import time
import uuid
import logging
from enum import Enum

logger = logging.getLogger(__name__)

SESSION_TTL = 300  # 5 minutes

ENTITY_ALIASES = {
    "name": "client_name",
    "client": "client_name",
    "customer": "client_name",
    "job": "job_type",
    "work": "job_type",
    "type": "job_type",
    "suburb": "location",
    "area": "location",
    "where": "location",
    "address": "location",
    "budget": "estimated_budget",
    "amount": "estimated_budget",
    "cost": "estimated_budget",
    "price": "estimated_budget",
    "materials": "materials_cost",
    "material": "materials_cost",
    "labor": "labor_cost",
    "labour": "labor_cost",
    "markup": "markup_percent",
    "lead": "lead_id",
    "lead_name": "lead_id",
    "quote": "quote_id",
    "quote_name": "quote_id",
    "description": "job_description",
    "job_desc": "job_description",
    "instruction": "text",
    "rule": "text",
    "cat": "category",
}

MONEY_WORDS = {
    "grand": 1000,
    "k": 1000,
    "thousand": 1000,
    "hundred": 100,
    "mil": 1000000,
    "million": 1000000,
}


def _normalize_entities(entities: dict, valid_params: list[str]) -> dict:
    """Map Gemini entity keys to PARAM_ORDER keys + parse money slang."""
    import re
    normalized = {}
    for key, val in entities.items():
        mapped_key = ENTITY_ALIASES.get(key, key)
        if mapped_key not in valid_params:
            if key in valid_params:
                mapped_key = key
            else:
                continue
        if mapped_key in ("estimated_budget", "materials_cost", "labor_cost", "amount", "markup_percent"):
            val = _parse_money(val)
        if val is not None:
            normalized[mapped_key] = val
    return normalized


def _parse_money(val) -> float | None:
    """Parse money values including slang like '5 grand', '8k', '15 thousand'."""
    import re
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        return None
    text = val.lower().strip().replace("$", "").replace(",", "")
    for word, multiplier in MONEY_WORDS.items():
        if word in text:
            numbers = re.findall(r'[\d.]+', text)
            if numbers:
                return float(numbers[0]) * multiplier
    numbers = re.findall(r'[\d.]+', text)
    if numbers:
        return float(numbers[0])
    return None


class SessionState(str, Enum):
    IDLE = "IDLE"
    CLASSIFYING = "CLASSIFYING"
    COLLECTING = "COLLECTING"
    CONFIRMING = "CONFIRMING"
    EXECUTING = "EXECUTING"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"


PARAM_ORDER = {
    "construction.lead.create": {
        "order": ["client_name", "job_type", "location", "estimated_budget", "urgency", "email"],
        "defaults": {"urgency": "medium"},
        "questions": {
            "client_name": "What's the client's name?",
            "job_type": "What kind of job?",
            "location": "Where?",
            "estimated_budget": "Budget estimate?",
            "urgency": "How urgent? (low/medium/high)",
            "email": "Client email?",
        },
    },
    "construction.quote.create": {
        "order": ["lead_id", "materials_cost", "labor_cost", "markup_percent"],
        "defaults": {"markup_percent": 20},
        "questions": {
            "lead_id": "Which lead is this for?",
            "materials_cost": "Materials cost?",
            "labor_cost": "Labor cost?",
            "markup_percent": "Markup percentage? (default 20%)",
        },
    },
    "construction.payment.record": {
        "order": ["quote_id", "amount"],
        "defaults": {},
        "questions": {
            "quote_id": "Which quote is this payment for?",
            "amount": "How much was paid?",
        },
    },
    "marketing.create_post": {
        "order": ["job_description", "suburb"],
        "defaults": {},
        "questions": {
            "job_description": "What was the job?",
            "suburb": "Which suburb?",
        },
    },
    "instructions.add": {
        "order": ["text", "category"],
        "defaults": {},
        "questions": {
            "text": "What's the instruction?",
            "category": "Category? (tone/workflow/priority/style/compliance)",
        },
    },
    "construction.quote.invoice": {
        "order": ["quote_id", "fuzzy", "fuzzy_ref"],
        "defaults": {},
        "questions": {
            "quote_id": "Which quote should I invoice?",
            "fuzzy": "Which quote?",
        },
    },
    "cross.quote_to_invoice": {
        "order": ["quote_id", "fuzzy", "fuzzy_ref"],
        "defaults": {},
        "questions": {
            "quote_id": "Which quote should I invoice?",
            "fuzzy": "Which quote?",
        },
    },
}

# Intents that need confirmation before executing
CONFIRM_REQUIRED = {
    "construction.lead.create",
    "construction.lead.update",
    "construction.lead.extract",
    "construction.quote.create",
    "construction.quote.update",
    "construction.quote.followup",
    "construction.quote.invoice",
    "construction.payment.record",
    "marketing.create_post",
    "instructions.add",
    "instructions.delete",
    "inbox.approve",
    "inbox.approve_batch",
    "cross.email_to_lead",
    "cross.lead_to_quote",
    "cross.quote_to_invoice",
    "meta.undo",
}

STRONG_CONFIRM = {
    "inbox.approve_batch",
    "construction.payment.record",
    "construction.quote.invoice",
}


class VoiceSession:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.state = SessionState.IDLE
        self.intent: str | None = None
        self.collected_params: dict = {}
        self.missing_params: list[str] = []
        self.next_question: str | None = None
        self.defaults: dict = {}
        self.last_entity: dict | None = None
        self.pending_action: dict | None = None
        self.undo_stack: list[dict] = []
        self.created_at = time.time()
        self.updated_at = time.time()

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.updated_at) > SESSION_TTL

    def touch(self):
        self.updated_at = time.time()

    def start_collecting(self, intent: str, initial_entities: dict | None = None):
        self.state = SessionState.COLLECTING
        self.intent = intent
        self.collected_params = {}
        self.defaults = {}

        config = PARAM_ORDER.get(intent)
        if not config:
            self.state = SessionState.IDLE
            return

        self.defaults = dict(config.get("defaults", {}))
        all_params = list(config["order"])

        if initial_entities:
            mapped = _normalize_entities(initial_entities, all_params)
            for key, val in mapped.items():
                self.collected_params[key] = val

        self.missing_params = [p for p in all_params if p not in self.collected_params]

        for param in list(self.missing_params):
            if param in self.defaults and param not in self.collected_params:
                pass

        if not self.missing_params:
            self._apply_defaults()
            self.state = SessionState.CONFIRMING
            self.next_question = None
        else:
            self.next_question = config["questions"].get(self.missing_params[0], f"What's the {self.missing_params[0]}?")

        self.touch()

    def add_param(self, key: str, value) -> str | None:
        self.collected_params[key] = value
        if key in self.missing_params:
            self.missing_params.remove(key)

        config = PARAM_ORDER.get(self.intent, {})
        questions = config.get("questions", {})

        if not self.missing_params:
            self._apply_defaults()
            self.state = SessionState.CONFIRMING
            self.next_question = None
            return None

        self.next_question = questions.get(self.missing_params[0], f"What's the {self.missing_params[0]}?")
        self.touch()
        return self.next_question

    def collect_next_param(self, value) -> str | None:
        if not self.missing_params:
            return None
        current_param = self.missing_params[0]
        return self.add_param(current_param, value)

    def _apply_defaults(self):
        for key, default_val in self.defaults.items():
            if key not in self.collected_params:
                self.collected_params[key] = default_val

    def set_confirming(self, pending_action: dict | None = None):
        self.state = SessionState.CONFIRMING
        self.pending_action = pending_action
        self.touch()

    def confirm(self) -> dict:
        self.state = SessionState.EXECUTING
        self.touch()
        return {
            "intent": self.intent,
            "params": dict(self.collected_params),
        }

    def cancel(self):
        self.state = SessionState.CANCELLED
        self.touch()

    def complete(self, result: dict | None = None):
        self.state = SessionState.COMPLETE
        if result and "entity" in result:
            self.last_entity = result["entity"]
        self.touch()

    def push_undo(self, action: dict):
        self.undo_stack.append({**action, "timestamp": time.time()})
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)

    def pop_undo(self) -> dict | None:
        if not self.undo_stack:
            return None
        entry = self.undo_stack.pop()
        if time.time() - entry.get("timestamp", 0) > 60:
            return None
        return entry

    def reset(self):
        self.state = SessionState.IDLE
        self.intent = None
        self.collected_params = {}
        self.missing_params = []
        self.next_question = None
        self.pending_action = None
        self.touch()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "intent": self.intent,
            "collected_params": self.collected_params,
            "missing_params": self.missing_params,
            "next_question": self.next_question,
            "defaults": self.defaults,
            "last_entity": self.last_entity,
            "created_at": self.created_at,
            "ttl": SESSION_TTL,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceSession":
        session = cls(session_id=data.get("session_id"))
        session.state = SessionState(data.get("state", "IDLE"))
        session.intent = data.get("intent")
        session.collected_params = data.get("collected_params", {})
        session.missing_params = data.get("missing_params", [])
        session.next_question = data.get("next_question")
        session.defaults = data.get("defaults", {})
        session.last_entity = data.get("last_entity")
        session.created_at = data.get("created_at", time.time())
        session.updated_at = time.time()
        return session


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, VoiceSession] = {}

    def get_or_create(self, session_id: str | None = None) -> VoiceSession:
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            if session.is_expired:
                logger.info(f"Session {session_id} expired, creating new")
                session.reset()
            return session

        session = VoiceSession(session_id=session_id)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> VoiceSession | None:
        session = self._sessions.get(session_id)
        if session and session.is_expired:
            session.reset()
        return session

    def delete(self, session_id: str):
        self._sessions.pop(session_id, None)

    def cleanup_expired(self):
        expired = [sid for sid, s in self._sessions.items() if s.is_expired]
        for sid in expired:
            del self._sessions[sid]


session_manager = SessionManager()
