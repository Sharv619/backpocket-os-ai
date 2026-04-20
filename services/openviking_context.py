"""
OpenViking context database integration (optional enhancement).

OpenViking runs as a sidecar: `openviking serve --port 7700`
If the server is not running, all methods fall back silently so the
existing SQLite/IFFilter RAG pipeline continues unaffected.
"""

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

OPENVIKING_BASE = os.getenv("OPENVIKING_URL", "http://localhost:7700")
_available: bool | None = None  # None = not yet checked


def _is_available() -> bool:
    global _available
    if _available is not None:
        return _available
    try:
        import httpx
        r = httpx.get(f"{OPENVIKING_BASE}/health", timeout=1.0)
        _available = r.status_code == 200
    except Exception:
        _available = False
    if not _available:
        logger.debug("OpenViking server not reachable — using built-in RAG only")
    return _available


def store_context(namespace: str, key: str, value: str) -> bool:
    """Persist a fact to OpenViking for future retrieval."""
    if not _is_available():
        return False
    try:
        import httpx
        httpx.post(
            f"{OPENVIKING_BASE}/context/{namespace}",
            json={"key": key, "value": value},
            timeout=2.0,
        )
        return True
    except Exception as e:
        logger.debug(f"OpenViking store failed: {e}")
        return False


def retrieve_context(namespace: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve relevant context chunks from OpenViking."""
    if not _is_available():
        return []
    try:
        import httpx
        r = httpx.post(
            f"{OPENVIKING_BASE}/context/{namespace}/search",
            json={"query": query, "top_k": top_k},
            timeout=2.0,
        )
        return r.json().get("results", []) if r.status_code == 200 else []
    except Exception as e:
        logger.debug(f"OpenViking retrieve failed: {e}")
        return []


def enrich_rag_context(existing_context: Dict[str, Any], query: str) -> Dict[str, Any]:
    """
    Merge OpenViking results into an existing RAG context dict.
    Safe to call unconditionally — no-ops if server is offline.
    """
    viking_results = retrieve_context("backpocket", query)
    if viking_results:
        existing_context["openviking_context"] = viking_results
        logger.info(f"OpenViking added {len(viking_results)} context chunks")
    return existing_context
