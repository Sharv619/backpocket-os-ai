"""
BackPocket OS — pgvector RAG Service
Replaces services/agentic_rag.py using Postgres pgvector for embeddings.
"""

import os
import json
import logging
from typing import Optional

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ═══════════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════════

DATABASE_URL = os.getenv(
    "POSTGRES_DB_URL", "postgresql+psycopg2://backpocket_user:backpocket_password@localhost:5432/backpocket_db"
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════
# pgvector RAG
# ═══════════════════════════════════════════════════════════════════════════


class PgvectorRAG:
    """Postgres pgvector-based RAG for semantic search."""

    _instance: Optional["PgvectorRAG"] = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._engine = create_engine(DATABASE_URL)
            cls._instance = instance
        return cls._instance

    @property
    def engine(self) -> Engine:
        return self._engine

    def get_embedding(self, text: str) -> list[float]:
        """Get embedding from Ollama."""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            # Fallback: return zero vector
            print(f"[WARN] Embedding failed: {e}")
            return [0.0] * 768

    def ingest(
        self,
        table: str,
        text: str,
        user_id: str,
        metadata: Optional[dict] = None,
    ) -> int:
        """Ingest text into vector store."""
        embedding = self.get_embedding(text)

        with self.engine.connect() as conn:
            if table == "knowledge_notes":
                result = conn.execute(
                    text(f"""
                        INSERT INTO {table} (user_id, body, tags, author_email, embedding)
                        VALUES (:user_id, :body, :tags, :author_email, :embedding::vector)
                        RETURNING id
                    """),
                    {
                        "user_id": user_id,
                        "body": text,
                        "tags": json.dumps(metadata.get("tags", []))
                        if metadata
                        else None,
                        "author_email": metadata.get("author_email", ""),
                        "embedding": embedding,
                    },
                )
            elif table == "pending_approvals":
                result = conn.execute(
                    text(f"""
                        INSERT INTO {table} 
                        (user_id, ref_id, sender, subject, preview, tier, embedding)
                        VALUES (:user_id, :ref_id, :sender, :subject, :preview, :tier, :embedding::vector)
                        RETURNING id
                    """),
                    {
                        "user_id": user_id,
                        "ref_id": metadata.get("ref_id", ""),
                        "sender": metadata.get("sender", ""),
                        "subject": metadata.get("subject", ""),
                        "preview": metadata.get("preview", ""),
                        "tier": metadata.get("tier", 3),
                        "embedding": embedding,
                    },
                )
            else:
                raise ValueError(f"Unknown table: {table}")

            conn.commit()
            return result.fetchone()[0]

    def retrieve(
        self,
        table: str,
        query: str,
        user_id: str,
        n: int = 5,
    ) -> list[dict]:
        """Retrieve similar texts via vector search."""
        query_embedding = self.get_embedding(query)

        with self.engine.connect() as conn:
            if table == "knowledge_notes":
                result = conn.execute(
                    text(f"""
                        SELECT id, body, tags, 
                        1 - (CAST(embedding AS vector) <=> :embedding::vector) as similarity
                        FROM {table}
                        WHERE user_id = :user_id
                        ORDER BY CAST(embedding AS vector) <=> :embedding::vector
                        LIMIT :n
                    """),
                    {
                        "embedding": query_embedding,
                        "user_id": user_id,
                        "n": n,
                    },
                )
            elif table == "pending_approvals":
                result = conn.execute(
                    text(f"""
                        SELECT id, subject, preview, tier,
                        1 - (CAST(embedding AS vector) <=> :embedding::vector) as similarity
                        FROM {table}
                        WHERE user_id = :user_id
                        ORDER BY CAST(embedding AS vector) <=> :embedding::vector
                        LIMIT :n
                    """),
                    {
                        "embedding": query_embedding,
                        "user_id": user_id,
                        "n": n,
                    },
                )
            else:
                return []

            return [dict(r._mapping) for r in result.fetchall()]

    def search_knowledge(
        self,
        query: str,
        user_id: str,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Search knowledge notes."""
        query_embedding = self.get_embedding(query)

        with self.engine.connect() as conn:
            # Format embedding as Postgres array string to avoid binding cast issues
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            sql = """
                SELECT id, category, title, body, tags,
                1 - (CAST(embedding AS vector) <=> CAST(:embedding AS vector)) as similarity
                FROM knowledge_notes
                WHERE user_id = :user_id
            """
            params = {"embedding": embedding_str, "user_id": user_id}
            
            if category:
                sql += " AND category = :category"
                params["category"] = category

            sql += " ORDER BY CAST(embedding AS vector) <=> CAST(:embedding AS vector) LIMIT 10"
            
            result = conn.execute(text(sql), params)
            return [dict(r._mapping) for r in result.fetchall()]

    def build_context(
        self,
        query: str,
        user_id: str,
        twin_type: str = "estimator",
    ) -> str:
        """Build RAG context for Twin AI."""
        personality = {
            "estimator": """You are Pip, BackPocket's estimator twin for Australian tradies.
Sound like a sharp operator in the business, not a generic AI assistant.
Default style:
- direct, grounded, practical
- short paragraphs or bullets only when useful
- no corporate fluff, no hype, no "as an AI", no robot disclaimers
- do the math cleanly and show assumptions when quoting, pricing, margin, GST, labour, or markup
- if details are missing, ask only for the exact missing inputs
- use AUD and Australian construction/business language naturally""",
            "site_manager": """You are Pip, BackPocket's site manager twin for Australian tradies.
Sound experienced, operational, and no-nonsense.
Default style:
- practical field advice, not generic AI wording
- structured, concise, safety-aware
- no corporate fluff, no "as an AI", no filler
- focus on sequencing, risks, materials, compliance, defects, and next actions""",
            "admin": """You are Pip, BackPocket's admin twin for Australian tradies.
Sound like a switched-on operations manager inside the business.
Default style:
- concise, clear, useful
- no generic AI phrasing, no fake enthusiasm, no padded intros
- help with follow-ups, scheduling, inbox triage, client comms, and keeping things moving
- when drafting copy, make it sound human and owner-led, not templated""",
        }.get(
            twin_type,
            """You are Pip from BackPocket.
Be direct, useful, and human. Never sound like a generic AI assistant.""",
        )

        # Get relevant knowledge
        results = self.search_knowledge(query, user_id)

        if results:
            context_parts = [personality, "\n## Relevant Knowledge:"]
            for r in results[:3]:
                context_parts.append(f"- {r.get('body', r.get('subject', ''))}")
        else:
            context_parts = [personality]

        return "\n\n".join(context_parts)


# ═══════════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════

_rag: Optional[PgvectorRAG] = None


def get_rag() -> PgvectorRAG:
    """Get RAG singleton."""
    global _rag
    if _rag is None:
        _rag = PgvectorRAG()
    return _rag


def ingest_to_rag(
    table: str,
    text: str,
    user_id: str,
    metadata: Optional[dict] = None,
) -> int:
    """Ingest text to RAG."""
    return get_rag().ingest(table, text, user_id, metadata)


def retrieve_from_rag(
    table: str,
    query: str,
    user_id: str,
    n: int = 5,
) -> list[dict]:
    """Retrieve from RAG."""
    return get_rag().retrieve(table, query, user_id, n)


# ═══════════════════════════════════════════════════════════════════════════
# Twin Engine Integration
# ═══════════════════════════════════════════════════════════════════════════


from services.gemini import get_openrouter_response

async def rag_chat(
    user_id: str,
    message: str,
    twin_type: str = "estimator",
    conversation_id: Optional[str] = None,
) -> dict:
    """Chat with RAG-augmented response while preserving Twin conversation history."""
    rag = get_rag()
    system_context = rag.build_context(message, user_id, twin_type)
    from services.memory import (
        auto_title_if_needed,
        create_conversation,
        get_conversation_messages,
        save_message_instant,
    )

    if not conversation_id:
        conversation_id = create_conversation(source="twin")

    save_message_instant(conversation_id, "user", message)
    prior_messages = get_conversation_messages(conversation_id, limit=12)
    history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in prior_messages[:-1]
        if msg.get("role") in {"user", "assistant"} and msg.get("content")
    ]

    # Layer 1: Gemini (free, fast)
    try:
        from services.gemini import get_gemini_client
        client = get_gemini_client()
        if client:
            history_lines = []
            for msg in history[-8:]:
                speaker = "User" if msg["role"] == "user" else "Pip"
                history_lines.append(f"{speaker}: {msg['content']}")

            full_prompt = (
                f"{system_context}\n\n"
                "Stay consistent with the existing thread. Match the user's tone.\n"
                "Do not reset into a generic assistant voice.\n"
            )
            if history_lines:
                full_prompt += "\nRecent conversation:\n" + "\n".join(history_lines)
            full_prompt += f"\n\nUser: {message}\nPip:"
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            if resp and resp.text:
                response_text = resp.text.strip()
                save_message_instant(conversation_id, "assistant", response_text)
                auto_title_if_needed(conversation_id)
                return {
                    "response": response_text,
                    "conversation_id": conversation_id,
                    "twin_type": twin_type,
                }
    except Exception as e:
        logger.warning(f"Gemini failed in rag_chat: {e}")

    # Layer 2: OpenRouter
    response = get_openrouter_response(
        prompt=(
            "Keep the response grounded and consistent with this thread.\n\n"
            + "\n".join(
                f"{'User' if msg['role'] == 'user' else 'Pip'}: {msg['content']}"
                for msg in history[-8:]
            )
            + f"\nUser: {message}\nPip:"
        ),
        model="openrouter/auto",
        sys_prompt=system_context,
        user_id=user_id
    )
    if response:
        response_text = response.strip()
        save_message_instant(conversation_id, "assistant", response_text)
        auto_title_if_needed(conversation_id)
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "twin_type": twin_type,
        }

    # Layer 3: Ollama local
    try:
        import ollama as _ollama
        msgs = [{"role": "system", "content": system_context}] + history[-8:] + [
            {"role": "user", "content": message}
        ]
        resp = _ollama.chat(model=os.getenv("OLLAMA_MODEL", "llama3.2"), messages=msgs)
        response_text = resp["message"]["content"].strip()
        save_message_instant(conversation_id, "assistant", response_text)
        auto_title_if_needed(conversation_id)
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "twin_type": twin_type,
        }
    except Exception as e:
        logger.warning(f"Ollama fallback failed in rag_chat: {e}")

    response_text = "I hit a model error just then. Send that again and I'll retry clean."
    save_message_instant(conversation_id, "assistant", response_text)
    return {
        "response": response_text,
        "conversation_id": conversation_id,
        "twin_type": twin_type,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Re-index Existing Data
# ═══════════════════════════════════════════════════════════════════════════


def reindex_all(user_id: str) -> dict:
    """Re-index all data for a user."""
    rag = get_rag()
    indexed = {"knowledge": 0, "emails": 0}

    with rag.engine.connect() as conn:
        # Re-index knowledge notes
        result = conn.execute(
            text(
                "SELECT id, body FROM knowledge_notes WHERE user_id = :uid AND embedding IS NULL"
            ),
            {"uid": user_id},
        )
        for row in result:
            try:
                rag.ingest("knowledge_notes", str(row[1]), user_id, {"id": row[0]})
                indexed["knowledge_notes"] += 1
            except Exception as e:
                print(f"[WARN] Failed to index knowledge note {row[0]}: {e}")

        # Re-index pending approvals
        result = conn.execute(
            text(
                "SELECT id, subject, draft_body FROM pending_approvals WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        for row in result:
            try:
                combined_text = f"{row[1]} {row[2]}"
                rag.ingest("pending_approvals", combined_text, user_id, {"ref_id": str(row[0])})
                indexed["pending_approvals"] += 1
            except Exception as e:
                print(f"[WARN] Failed to index pending approval {row[0]}: {e}")

        conn.commit()

    return indexed
