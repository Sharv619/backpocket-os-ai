from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query
from fastapi.responses import Response
import asyncio
import base64
import logging
import os
from typing import Optional
from services.document_vision import (
    save_document,
    get_all_documents,
    get_document,
    analyze_document,
    delete_document,
    analyze_building_image,
)
import services.paperless as paperless

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger(__name__)

_PAPERLESS_ENABLED = bool(os.getenv("PAPERLESS_TOKEN", ""))


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(request: Request):
    """
    Upload a document. Accepts:
      - application/json: {'file': '<base64>', 'filename': '...', 'category': '...'}
      - multipart/form-data: file field + optional category field
    Paperless-ngx used when PAPERLESS_TOKEN is set, else local SQLite.
    """
    try:
        content: bytes
        filename: str
        category: str = "other"

        ct = request.headers.get("content-type", "")

        if "application/json" in ct:
            body = await request.json()
            raw = body.get("file", "")
            filename = body.get("filename", "document.jpg")
            category = body.get("category", "other")
            if not raw:
                return {"status": "error", "message": "No file data in JSON body"}
            # Strip data-URI prefix if present (e.g. "data:image/jpeg;base64,...")
            if "," in raw:
                raw = raw.split(",", 1)[1]
            content = base64.b64decode(raw)

        elif "multipart" in ct:
            form = await request.form()
            upload = form.get("file")
            if upload is None:
                return {"status": "error", "message": "No file field in form"}
            filename = getattr(upload, "filename", None) or "document.jpg"
            category = str(form.get("category", "other"))
            content = await upload.read()
            # Strip accidental multipart wrapper
            if content.startswith(b"------"):
                h = content.find(b"\r\n\r\n")
                if h > 0:
                    nb = content.find(b"\r\n------", h)
                    content = content[h + 4: nb] if nb > 0 else content[h + 4:]

        else:
            # Raw body fallback (shouldn't happen but be forgiving)
            content = await request.body()
            filename = "document.jpg"
            if len(content) < 100:
                return {"status": "error", "message": "No file provided"}

        if len(content) < 100:
            return {"status": "error", "message": "File too small or invalid"}

        # ── Store in Paperless (primary) ──────────────────────────────────────
        if _PAPERLESS_ENABLED:
            loop = asyncio.get_event_loop()
            # Infer document type from category for auto-tagging
            doc_type_name = _category_to_doc_type(category)
            result = await loop.run_in_executor(
                None,
                lambda: paperless.upload_document(
                    content,
                    filename,
                    title=os.path.splitext(filename)[0],
                    document_type=doc_type_name,
                ),
            )
            if "error" not in result:
                # Also save locally so analyze endpoint still works
                doc_id = save_document(content, filename, category=category)
                return {
                    "status": "success",
                    "document_id": doc_id,
                    "paperless_task_id": result.get("task_id"),
                    "filename": filename,
                    "message": "Uploaded to Paperless-ngx (OCR queued)",
                    "storage": "paperless",
                }
            logger.warning(f"Paperless upload failed ({result['error']}), falling back to local")

        # ── Fallback: local SQLite store ──────────────────────────────────────
        doc_id = save_document(content, filename, category=category)
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename,
            "message": "Document uploaded",
            "storage": "local",
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return {"status": "error", "message": str(e)}


def _category_to_doc_type(category: str) -> str:
    return {
        "invoice": "Invoice",
        "receipt": "Receipt",
        "quote": "Quote",
        "contract": "Contract",
        "permit": "Permit",
        "photo": "Photo",
        "other": "Miscellaneous",
    }.get(category.lower(), "Miscellaneous")


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("")
async def list_documents(
    query: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    """
    List documents. Returns Paperless docs when configured, falls back to
    local SQLite store.
    """
    try:
        if _PAPERLESS_ENABLED:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: paperless.list_documents(page=page, page_size=page_size, query=query),
            )
            if "error" not in result:
                return {
                    "count": result["count"],
                    "documents": result["results"],
                    "storage": "paperless",
                    "paperless_ui": f"{os.getenv('PAPERLESS_URL', 'http://localhost:8010')}/documents/",
                }
            logger.warning(f"Paperless list failed: {result['error']}")

        docs = get_all_documents()
        return {"count": len(docs), "documents": docs, "storage": "local"}
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return {"status": "error", "message": str(e)}


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/thumbnail/{paperless_id}")
async def proxy_thumbnail(paperless_id: int):
    """Proxy Paperless thumbnail so Flutter doesn't need direct Paperless access."""
    if not _PAPERLESS_ENABLED:
        raise HTTPException(status_code=404, detail="Paperless not configured")
    try:
        import requests as req_lib
        resp = req_lib.get(
            f"{os.getenv('PAPERLESS_URL', 'http://localhost:8010')}/api/documents/{paperless_id}/thumb/",
            headers={"Authorization": f"Token {os.getenv('PAPERLESS_TOKEN')}"},
            timeout=15,
        )
        return Response(content=resp.content, media_type=resp.headers.get("content-type", "image/png"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/download/{paperless_id}")
async def proxy_download(paperless_id: int):
    """Proxy Paperless PDF download."""
    if not _PAPERLESS_ENABLED:
        raise HTTPException(status_code=404, detail="Paperless not configured")
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(None, paperless.download_document, paperless_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=document_{paperless_id}.pdf"},
    )


@router.get("/meta")
async def get_paperless_meta():
    """Return correspondents, document types, tags for Flutter filter UI."""
    if not _PAPERLESS_ENABLED:
        return {"paperless": False}
    loop = asyncio.get_event_loop()
    correspondents, doc_types, tags = await asyncio.gather(
        loop.run_in_executor(None, paperless.list_correspondents),
        loop.run_in_executor(None, paperless.list_document_types),
        loop.run_in_executor(None, paperless.list_tags),
    )
    return {
        "paperless": True,
        "paperless_ui": f"{os.getenv('PAPERLESS_URL', 'http://localhost:8010')}/documents/",
        "correspondents": correspondents,
        "document_types": doc_types,
        "tags": tags,
    }


@router.get("/{doc_id}")
async def get_document_detail(doc_id: int):
    """Get single document — tries Paperless first, falls back to local."""
    try:
        if _PAPERLESS_ENABLED:
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(None, paperless.get_document, doc_id)
            if "error" not in doc:
                return doc
        doc = get_document(doc_id)
        if doc:
            return doc
        return {"status": "error", "message": "Document not found"}
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return {"status": "error", "message": str(e)}


# ── Analyse (local AI vision — works with or without Paperless) ───────────────

@router.post("/analyze/{doc_id}")
async def analyze_document_endpoint(doc_id: int):
    """Analyse document with AI (local vision pipeline)."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, analyze_document, doc_id)
        return result
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/analyze-material")
async def analyze_material_endpoint(
    file: UploadFile = File(...),
    analysis_type: str = "material",
):
    """
    Analyse a building/site photo for materials or structural damage.
    analysis_type: 'material' | 'damage'
    """
    if analysis_type not in ("material", "damage"):
        raise HTTPException(status_code=400, detail="analysis_type must be 'material' or 'damage'")
    try:
        content = await file.read()
        image_b64 = base64.b64encode(content).decode()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, analyze_building_image, image_b64, analysis_type)
        return result
    except Exception as e:
        logger.error(f"Material analysis error: {e}")
        return {"status": "error", "message": str(e)}


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{doc_id}")
async def delete_document_endpoint(doc_id: int):
    """Delete a document from local store (Paperless deletion requires web UI)."""
    try:
        delete_document(doc_id)
        return {"status": "success", "message": "Document deleted"}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return {"status": "error", "message": str(e)}
