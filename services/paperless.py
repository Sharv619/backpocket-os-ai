"""
Paperless-ngx REST API wrapper.

Set PAPERLESS_URL and PAPERLESS_TOKEN in .env.
If PAPERLESS_TOKEN is empty, all methods return graceful fallbacks so the
rest of the app keeps working without Paperless running.
"""
import io
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

PAPERLESS_URL = os.getenv("PAPERLESS_URL", "http://localhost:8010").rstrip("/")
PAPERLESS_TOKEN = os.getenv("PAPERLESS_TOKEN", "")


def is_available() -> bool:
    return bool(PAPERLESS_TOKEN)


def _headers() -> dict:
    return {"Authorization": f"Token {PAPERLESS_TOKEN}"}


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_document(
    content: bytes,
    filename: str,
    title: Optional[str] = None,
    correspondent: Optional[str] = None,
    document_type: Optional[str] = None,
    tags: Optional[list[int]] = None,
) -> dict:
    """
    POST to /api/documents/post_document/
    Returns {"paperless_id": int, "task_id": str} on success.
    Returns {"error": str} on failure.
    """
    if not is_available():
        return {"error": "Paperless not configured"}

    data: dict = {}
    if title:
        data["title"] = title
    if correspondent:
        data["correspondent"] = correspondent
    if document_type:
        data["document_type"] = document_type
    if tags:
        for tag in tags:
            data.setdefault("tags", []).append(tag)

    try:
        resp = requests.post(
            f"{PAPERLESS_URL}/api/documents/post_document/",
            headers=_headers(),
            files={"document": (filename, io.BytesIO(content), _mime_type(filename))},
            data=data,
            timeout=60,
        )
        resp.raise_for_status()
        # Paperless returns the async task UUID as plain text or JSON
        task_id = resp.text.strip().strip('"')
        return {"task_id": task_id, "filename": filename}
    except requests.RequestException as e:
        logger.error(f"Paperless upload error: {e}")
        return {"error": str(e)}


def _mime_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "tiff": "image/tiff",
        "tif": "image/tiff",
    }.get(ext, "application/octet-stream")


# ── List & fetch ──────────────────────────────────────────────────────────────

def list_documents(page: int = 1, page_size: int = 25, query: str = "") -> dict:
    """
    GET /api/documents/?page=&page_size=&query=
    Returns {"count": int, "results": [...]} or {"error": str}.
    """
    if not is_available():
        return {"count": 0, "results": [], "error": "Paperless not configured"}

    params: dict = {"page": page, "page_size": page_size}
    if query:
        params["query"] = query

    try:
        resp = requests.get(
            f"{PAPERLESS_URL}/api/documents/",
            headers=_headers(),
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        # Normalise to our shape
        results = [_normalise_doc(d) for d in data.get("results", [])]
        return {"count": data.get("count", len(results)), "results": results}
    except requests.RequestException as e:
        logger.error(f"Paperless list error: {e}")
        return {"count": 0, "results": [], "error": str(e)}


def get_document(doc_id: int) -> dict:
    """GET /api/documents/{id}/"""
    if not is_available():
        return {"error": "Paperless not configured"}
    try:
        resp = requests.get(
            f"{PAPERLESS_URL}/api/documents/{doc_id}/",
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return _normalise_doc(resp.json())
    except requests.RequestException as e:
        logger.error(f"Paperless get_document error: {e}")
        return {"error": str(e)}


def download_document(doc_id: int) -> Optional[bytes]:
    """GET /api/documents/{id}/download/"""
    if not is_available():
        return None
    try:
        resp = requests.get(
            f"{PAPERLESS_URL}/api/documents/{doc_id}/download/",
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as e:
        logger.error(f"Paperless download error: {e}")
        return None


def get_thumbnail_url(doc_id: int) -> str:
    """Returns proxied thumbnail URL (served via our FastAPI, not direct to Paperless)."""
    return f"/api/documents/thumbnail/{doc_id}"


# ── Metadata helpers ──────────────────────────────────────────────────────────

def list_correspondents() -> list[dict]:
    return _list_meta("correspondents")


def list_document_types() -> list[dict]:
    return _list_meta("document_types")


def list_tags() -> list[dict]:
    return _list_meta("tags")


def _list_meta(endpoint: str) -> list[dict]:
    if not is_available():
        return []
    try:
        resp = requests.get(
            f"{PAPERLESS_URL}/api/{endpoint}/",
            headers=_headers(),
            params={"page_size": 100},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.RequestException as e:
        logger.error(f"Paperless {endpoint} error: {e}")
        return []


def ensure_correspondent(name: str) -> Optional[int]:
    """Get or create a correspondent by name, return its ID."""
    if not is_available() or not name:
        return None
    existing = list_correspondents()
    for c in existing:
        if c.get("name", "").lower() == name.lower():
            return c["id"]
    try:
        resp = requests.post(
            f"{PAPERLESS_URL}/api/correspondents/",
            headers={**_headers(), "Content-Type": "application/json"},
            json={"name": name},
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("id")
    except requests.RequestException:
        pass
    return None


def ensure_document_type(name: str) -> Optional[int]:
    """Get or create a document type by name, return its ID."""
    if not is_available() or not name:
        return None
    existing = list_document_types()
    for dt in existing:
        if dt.get("name", "").lower() == name.lower():
            return dt["id"]
    try:
        resp = requests.post(
            f"{PAPERLESS_URL}/api/document_types/",
            headers={**_headers(), "Content-Type": "application/json"},
            json={"name": name},
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("id")
    except requests.RequestException:
        pass
    return None


# ── Normalise Paperless doc → our shape ──────────────────────────────────────

def _normalise_doc(d: dict) -> dict:
    return {
        "id": d.get("id"),
        "paperless_id": d.get("id"),
        "title": d.get("title", "Untitled"),
        "filename": d.get("original_file_name", ""),
        "created": d.get("created", ""),
        "added": d.get("added", ""),
        "correspondent": d.get("correspondent"),
        "document_type": d.get("document_type"),
        "tags": d.get("tags", []),
        "content": (d.get("content") or "")[:300],  # OCR preview
        "archived_file_name": d.get("archived_file_name", ""),
        "thumbnail_url": f"/api/documents/thumbnail/{d.get('id')}",
        "download_url": f"/api/documents/download/{d.get('id')}",
        "paperless_url": f"{PAPERLESS_URL}/documents/{d.get('id')}/details",
    }
