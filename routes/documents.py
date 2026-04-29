from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query
from fastapi.responses import Response
import asyncio
import base64
import logging
import os
from services.document_vision import (
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
    New workflow (Native MVP OCR + Local AI Extractor):
    1. Reads the uploaded file bytes.
    2. Saves the document to the local database to get a valid doc_id.
    3. Runs native PyPDF2 extraction (or flags for Gemini Vision).
    4. Runs the local Ollama extractor to parse line items and save to DB.
    """
    from services.documents.ocr import process_document
    from services.documents.extractor import extract_document_entities
    from services.document_vision import save_document
    
    try:
        content, filename, category = await _extract_file_from_request(request)
        if len(content) < 100:
            return {"status": "error", "message": "File too small or invalid"}

        mime_type = "application/pdf" if filename.lower().endswith(".pdf") else "image/jpeg"
        
        # Save the document first so we have a valid ID for the /analyze endpoint
        doc_id = save_document(content, filename, category)

        # 1. OCR Extraction
        ocr_result = process_document(content, filename, mime_type)
        
        # 2. AI Extraction (if we got text natively)
        extracted_data = {}
        if ocr_result["status"] == "success":
            user_id = getattr(request.state, "user_id", "00000000-0000-0000-0000-000000000000")
            extracted_data = extract_document_entities(ocr_result["content"], filename, user_id=user_id)

        # Always return success so the frontend proceeds to call /analyze/{doc_id}
        return {
            "status": "success",
            "message": "Document uploaded successfully.",
            "document_id": doc_id,
            "ocr_content": ocr_result["content"],
            "filename": filename,
            "extracted_data": extracted_data
        }

    except Exception as e:
        logger.error(f"Native OCR upload error: {e}")
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
        if upload is None or not hasattr(upload, "filename"):
            raise ValueError("No file field in form")
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

@router.post("/query")
async def vision_query_endpoint(
    request: Request,
    file: UploadFile = File(...),
    query: str = Query(...),
):
    """
    Prompt 2: Photo-to-Query (Measurements/Materials).
    Accepts multipart/form-data upload (image file) + query string.
    """
    from services.document_vision import vision_query_gemini
    try:
        # Safe file buffering (Prompt 2 requirement)
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty image file")
            
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, vision_query_gemini, content, query)
        
        if "error" in result:
            return {"status": "error", "message": result["error"]}
            
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Vision query error: {e}")
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
