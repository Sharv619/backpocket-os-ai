"""
Twin Engine — Agentic RAG system for BackPocket.
Ported from backpocket-os/agents/twin_system.py.
Uses ChromaDB for vector RAG + Gemini as the LLM (Ollama fallback).
Three specialized twins: Estimator, Site Manager, Admin.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TWINS_DIR = Path(os.path.expanduser("~/.backpocket/twins"))
CHROMADB_DIR = Path(os.path.expanduser("~/.backpocket/chromadb"))
TWINS_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(parents=True, exist_ok=True)


# ── Twin types ─────────────────────────────────────────────────────────────────

class TwinType(Enum):
    ACCOUNTANT = "estimator"
    AUDITOR    = "site_manager"
    ADMIN      = "admin"


PERSONALITIES: dict[TwinType, dict] = {
    TwinType.ACCOUNTANT: {
        "name": "Estimator Twin",
        "description": "Handles Measurements, parsing Construction Leads, and calculating Quotes/Payments.",
        "system_prompt": """You are the Estimator Twin for a sole trader construction business in Australia.
You handle: Measurements, parsing Construction Leads, and calculating Quotes/Payments.
Be accurate, compliant, practical. Use AUD.""",
        "capabilities": ["leads", "quotes", "payments", "measurements"],
    },
    TwinType.AUDITOR: {
        "name": "Site Manager Twin",
        "description": "Handles Documents (OCR scanning of receipts/materials) and pushes Marketing posts.",
        "system_prompt": """You are the Site Manager Twin for a sole trader construction business in Australia.
You handle: Documents (OCR scanning of receipts/materials) and pushing Marketing posts from completed jobs.
Be thorough and organized.""",
        "capabilities": ["documents", "ocr", "marketing", "materials"],
    },
    TwinType.ADMIN: {
        "name": "Admin Twin",
        "description": "Handles email, scheduling, follow-ups, and routine admin automation",
        "system_prompt": """You are the Admin Twin for a sole trader business in Australia.
You handle: email triage, scheduling, client follow-ups, reminders, admin automation.
You know: Australian business communication standards, client management best practices.
Be proactive. Offer specific help and follow through on tasks.""",
        "capabilities": ["email_management", "scheduling", "reminders", "client_management"],
    },
}


def get_ai_provider():
    """Reads the AI_PROVIDER from .env and returns the correct service class instance."""
    provider = os.getenv("AI_PROVIDER", "openrouter").lower()

    if provider == "ollama":
        from services.ollama_service import OllamaService
        return OllamaService()
    
    # Default to OpenRouter
    from services.openrouter_service import OpenRouterService
    return OpenRouterService()


class TwinEngine:
    """
    Unified engine for making AI calls.
    Uses the provider model to switch between cloud and local.
    """
    def __init__(self):
        self.provider = get_ai_provider()
        logger.info(f"TwinEngine initialized with AI provider: {self.provider.__class__.__name__}")

    def get_completion(self, prompt: str, model: str = None) -> str:
        """
        Gets a text completion from the configured AI provider.
        """
        return self.provider.analyze(prompt, model=model)

    def get_vision_completion(self, prompt: str, image_b64: str, model: str = None) -> str:
        """
        Gets a vision completion from the configured AI provider.
        """
        return self.provider.analyze_vision(prompt, image_b64, model=model)


# ── ChromaDB RAG ───────────────────────────────────────────────────────────────

class RAGContextBuilder:
    """Build context from ChromaDB vector store."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                self._client = chromadb.PersistentClient(
                    path=str(CHROMADB_DIR),
                    settings=Settings(anonymized_telemetry=False),
                )
            except Exception as e:
                logger.warning(f"ChromaDB unavailable: {e}")
                return None
        return self._client

    def ingest(self, twin_type: TwinType, doc_id: str, text: str, metadata: dict = None):
        """Add a document chunk to the vector store."""
        client = self._get_client()
        if not client:
            return False
        try:
            collection = client.get_or_create_collection(name=twin_type.value)
            collection.upsert(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata or {}],
            )
            return True
        except Exception as e:
            logger.warning(f"RAG ingest failed: {e}")
            return False

    def retrieve(self, twin_type: TwinType, query: str, n: int = 5) -> list[str]:
        """Retrieve relevant chunks for a query, then IF-filter before returning."""
        client = self._get_client()
        if not client:
            return []
        try:
            collection = client.get_or_create_collection(name=twin_type.value)
            # Fetch 2× requested so IF has enough to filter from
            results = collection.query(query_texts=[query], n_results=n * 2)
            chunks = results.get("documents", [[]])[0]
            if not chunks:
                return []
            from services.if_filter import IFFilter
            clean, diag = IFFilter.filter_rag_chunks(chunks, query=query, top_n=n)
            logger.debug(f"RAG IF: {diag}")
            return clean
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    async def build_context(self, twin_type: TwinType, query: str) -> str:
        """Build full system context: personality + RAG chunks."""
        personality = PERSONALITIES[twin_type]
        parts = [personality["system_prompt"]]

        chunks = self.retrieve(twin_type, query)
        if chunks:
            parts.append("\n## Relevant Knowledge:")
            for chunk in chunks:
                parts.append(f"- {chunk}")

        return "\n\n".join(parts)


rag = RAGContextBuilder()


# ── LLM call ──────────────────────────────────────────────────────────────────

def _call_llm(system_context: str, messages: list[dict]) -> str:
    """Gemini first, Ollama fallback, static fallback."""
    # Try Gemini
    try:
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        history = []
        for m in messages[:-1]:  # all but last user turn
            history.append({"role": m["role"], "parts": [{"text": m["content"]}]})
        last_msg = messages[-1]["content"]
        full_prompt = system_context + "\n\n" + last_msg
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
        return resp.text
    except Exception as e:
        logger.warning(f"Gemini failed in twin engine: {e}")

    # Try Ollama
    try:
        import ollama as _ollama
        msgs = [{"role": "system", "content": system_context}] + messages
        resp = _ollama.chat(model=os.getenv("OLLAMA_MODEL", "all-minilm:l6-v2"), messages=msgs)
        return resp["message"]["content"]
    except Exception as e:
        logger.warning(f"Ollama failed in twin engine: {e}")

    return "I'm having trouble connecting to the AI right now. Please try again in a moment."


# ── Storage ────────────────────────────────────────────────────────────────────

class TwinStorage:
    def __init__(self):
        self.conv_path = TWINS_DIR / "conversations"
        self.conv_path.mkdir(exist_ok=True)

    def save(self, conv: dict):
        f = self.conv_path / f"{conv['conversation_id']}.json"
        f.write_text(json.dumps(conv, indent=2, default=str))

    def load(self, conv_id: str) -> Optional[dict]:
        f = self.conv_path / f"{conv_id}.json"
        if not f.exists():
            return None
        return json.loads(f.read_text())

    def list(self, twin_type: str = None) -> list[dict]:
        convs = []
        for f in self.conv_path.glob("*.json"):
            try:
                c = json.loads(f.read_text())
                if twin_type is None or c.get("twin_type") == twin_type:
                    convs.append(c)
            except Exception:
                continue
        return sorted(convs, key=lambda c: c.get("updated_at", ""), reverse=True)


storage = TwinStorage()


# ── Main engine ────────────────────────────────────────────────────────────────

async def twin_chat(
    twin_type_str: str,
    message: str,
    conversation_id: str = None,
) -> dict:
    """
    Send a message to a twin and get a response with RAG context.
    Returns: {response, conversation_id, twin_type}
    """
    twin_type = TwinType(twin_type_str.lower()) if twin_type_str.lower() in [t.value for t in TwinType] else TwinType.ACCOUNTANT

    # Load or create conversation
    conv = None
    if conversation_id:
        conv = storage.load(conversation_id)
    if conv is None:
        conv = {
            "conversation_id": str(uuid.uuid4()),
            "twin_type": twin_type.value,
            "title": f"Chat {datetime.now().strftime('%Y-%m-%d')}",
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    conv["messages"].append({"role": "user", "content": message})

    # Build RAG-augmented system context
    system_context = await rag.build_context(twin_type, message)

    # Build message history for LLM (last 10)
    history = [{"role": m["role"], "content": m["content"]} for m in conv["messages"][-10:]]

    response = _call_llm(system_context, history)

    conv["messages"].append({"role": "assistant", "content": response})
    conv["updated_at"] = datetime.now().isoformat()
    storage.save(conv)

    return {
        "response": response,
        "conversation_id": conv["conversation_id"],
        "twin_type": twin_type.value,
        "twin_name": PERSONALITIES[twin_type]["name"],
    }


def list_twins() -> list[dict]:
    return [
        {
            "type": t.value,
            "name": PERSONALITIES[t]["name"],
            "description": PERSONALITIES[t]["description"],
            "capabilities": PERSONALITIES[t]["capabilities"],
        }
        for t in TwinType
    ]


def ingest_document(twin_type_str: str, doc_id: str, text: str, metadata: dict = None) -> bool:
    """Index a document into the vector store for a given twin."""
    twin_type = TwinType(twin_type_str.lower()) if twin_type_str.lower() in [t.value for t in TwinType] else TwinType.ACCOUNTANT
    return rag.ingest(twin_type, doc_id, text, metadata)
