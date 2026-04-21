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
async def upload_document_and_analyze(request: Request):
    """
    New workflow:
    1. Uploads a document to Paperless-ngx.
    2. Polls for the OCR task to complete.
    3. Fetches the extracted text from Paperless.
    4. Submits the clean text to a language model for semantic analysis.
    """
    if not _PAPERLESS_ENABLED:
        return HTTPException(status_code=503, detail="Paperless-ngx service is not configured.")

    try:
        # Step 0: Extract file content from the request (same as before)
        content, filename, category = await _extract_file_from_request(request)
        if len(content) < 100:
            return {"status": "error", "message": "File too small or invalid"}

        # Step 1: Upload to Paperless and get a task ID
        loop = asyncio.get_event_loop()
        upload_result = await loop.run_in_executor(
            None,
            lambda: paperless.upload_document(
                content,
                filename,
                title=os.path.splitext(filename)[0],
                document_type=_category_to_doc_type(category),
            ),
        )

        if "error" in upload_result:
            raise HTTPException(status_code=502, detail=f"Paperless upload failed: {upload_result['error']}")
        
        task_id = upload_result.get("task_id")
        if not task_id:
            raise HTTPException(status_code=500, detail="Paperless did not return a task ID.")

        # Step 2: Poll for task completion to get the document ID
        doc_id = None
        for _ in range(15): # Poll for up to 30 seconds
            await asyncio.sleep(2)
            status_result = await loop.run_in_executor(None, paperless.get_task_status, task_id)
            if status_result.get("status") == "SUCCESS":
                doc_id = status_result.get("document_id")
                break
            elif status_result.get("status") == "FAILURE":
                raise HTTPException(status_code=500, detail=f"Paperless processing failed: {status_result.get('error')}")
        
        if not doc_id:
            raise HTTPException(status_code=504, detail="Timeout waiting for Paperless to process the document.")

        # Step 3: Fetch the full document details, including OCR'd content
        paperless_doc = await loop.run_in_executor(None, paperless.get_document, doc_id)
        if "error" in paperless_doc:
            raise HTTPException(status_code=502, detail=f"Could not fetch processed document from Paperless: {paperless_doc['error']}")
        
        ocr_content = paperless_doc.get("content", "")
        if not ocr_content:
            # If content is empty, it might not be an error, but we can't analyze.
            # We'll save a local record and return a success message without AI analysis.
            local_doc_id = save_document(content, filename, category=category)
            return {"status": "success_no_analysis", "document_id": local_doc_id, "paperless_id": doc_id, "message": "Document uploaded and OCR'd, but no text was found to analyze."}

        # Step 4: Save a local reference and submit the text for AI analysis
        local_doc_id = save_document(content, filename, category=category)
        
        from services.document_vision import analyze_text_content
        analysis_result = await loop.run_in_executor(None, analyze_text_content, local_doc_id, ocr_content)

        return {
            "status": "success",
            "document_id": local_doc_id,
            "paperless_id": doc_id,
            "analysis": analysis_result,
            "message": "Document uploaded, OCR'd, and analyzed."
        }

    except Exception as e:
        logger.error(f"New upload workflow error: {e}")
        # Use HTTPException's error handling if it's one of those, otherwise generic error
        if isinstance(e, HTTPException):
            raise
        return {"status": "error", "message": str(e)}

async def _extract_file_from_request(request: Request):
    """Helper to get file content, name, and category from different request types."""
    content: bytes
    filename: str
    category: str = "other"
    ct = request.headers.get("content-type", "")

    if "application/json" in ct:
        body = await request.json()
        raw = body.get("file", "")
        filename = body.get("filename", "document.jpg")
        category = body.get("category", "other")
        if not raw: raise ValueError("No file data in JSON body")
        if "," in raw: raw = raw.split(",", 1)[1]
        content = base64.b64decode(raw)
    elif "multipart" in ct:
        form = await request.form()
        upload = form.get("file")
        if not isinstance(upload, UploadFile): raise ValueError("No file field in form")
        filename = upload.filename or "document.jpg"
        category = str(form.get("category", "other"))
        content = await upload.read()
    else:
        raise ValueError(f"Unsupported content type: {ct}")
        
    return content, filename, category



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
