"""
BackPocket OS — pgvector RAG Service
Replaces services/agentic_rag.py using Postgres pgvector for embeddings.
"""

import os
import json
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

# ═══════════════════════════════════════════════════════════════════════════════════
# pgvector RAG
# ═══════════════════════════════════════════════════════════════════════════


class PgvectorRAG:
    """Postgres pgvector-based RAG for semantic search."""

    _instance: Optional["PgvectorRAG"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine = create_engine(DATABASE_URL)
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
                    text("""
                        INSERT INTO knowledge_notes (user_id, body, tags, author_email, embedding)
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
                    text("""
                        INSERT INTO pending_approvals 
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
                    text("""
                        SELECT id, body, tags, 
                        1 - (embedding <=> :embedding::vector) as similarity
                        FROM knowledge_notes
                        WHERE user_id = :user_id
                        ORDER BY embedding <=> :embedding::vector
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
                    text("""
                        SELECT id, subject, preview, tier,
                        1 - (embedding <=> :embedding::vector) as similarity
                        FROM pending_approvals
                        WHERE user_id = :user_id
                        ORDER BY embedding <=> :embedding::vector
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
                1 - (embedding <=> CAST(:embedding AS vector)) as similarity
                FROM knowledge_notes
                WHERE user_id = :user_id
            """
            params = {"embedding": embedding_str, "user_id": user_id}
            
            if category:
                sql += " AND category = :category"
                params["category"] = category

            sql += " ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT 10"
            
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
            "estimator": """You are Pip, the BackPocket estimator twin. 
Be friendly, practical, and help with tax and invoicing.""",
            "site_manager": """You are Pip, the BackPocket site_manager twin.
Be thorough, detail-oriented, and help with compliance.""",
            "admin": """You are Pip, the BackPocket admin twin.
Be efficient, organized, and help with operations.""",
        }.get(twin_type, "You are Pip, the BackPocket AI assistant.")

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

async def rag_chat(user_id: str, message: str, twin_type: str = "estimator") -> str:
    """Chat with RAG-augmented response using OpenRouter."""
    rag = get_rag()

    # Build context (Personality + RAG Knowledge)
    system_context = rag.build_context(message, user_id, twin_type)

    # Call AI (prefer OpenRouter auto for cost/quality balance)
    response = get_openrouter_response(
        prompt=message,
        model="openrouter/auto",
        sys_prompt=system_context,
        user_id=user_id
    )

    if not response:
        # Fallback to a simple message if AI fails
        return "I'm sorry, I'm having trouble thinking clearly right now. Can you try again?"

    return response


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
        for row in result.fetchall():
            try:
                rag.ingest("knowledge_notes", row[1], user_id, {"id": row[0]})
                indexed["knowledge"] += 1
            except Exception as e:
                print(f"[WARN] Failed to index knowledge {row[0]}: {e}")

        # Re-index pending approvals
        result = conn.execute(
            text(
                "SELECT id, subject, preview FROM pending_approvals WHERE user_id = :uid AND embedding IS NULL"
            ),
            {"uid": user_id},
        )
        for row in result.fetchall():
            try:
                text = f"{row[1]} {row[2]}"
                rag.ingest("pending_approvals", text, user_id, {"ref_id": str(row[0])})
                indexed["emails"] += 1
            except Exception as e:
                print(f"[WARN] Failed to index email {row[0]}: {e}")

        conn.commit()

    return indexed
