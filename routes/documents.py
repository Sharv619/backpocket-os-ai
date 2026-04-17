from fastapi import APIRouter, Request, UploadFile, File, HTTPException
import logging
import os
import uuid
from typing import List
from services.document_vision import (
    save_document,
    get_all_documents,
    get_document,
    analyze_document,
    delete_document,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), category: str = "other"):
    """Upload a document (image/file)."""
    try:
        filename = file.filename or "document.jpg"
        content = await file.read()

        # Handle potential form data wrapper
        if content.startswith(b"------"):
            header_end = content.find(b"\r\n\r\n")
            if header_end > 0:
                next_boundary = content.find(b"\r\n------", header_end)
                if next_boundary > 0:
                    content = content[header_end + 4 : next_boundary]

        if len(content) < 100:
            return {"status": "error", "message": "File too small or invalid"}

        doc_id = save_document(content, filename, category=category)
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename,
            "message": "Document uploaded",
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("")
async def list_documents():
    """Get all documents."""
    try:
        docs = get_all_documents()
        return {"count": len(docs), "documents": docs}
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/{doc_id}")
async def get_document_detail(doc_id: int):
    """Get single document."""
    try:
        doc = get_document(doc_id)
        if doc:
            return doc
        return {"status": "error", "message": "Document not found"}
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/analyze/{doc_id}")
async def analyze_document_endpoint(doc_id: int):
    """Analyze document with AI."""
    try:
        result = analyze_document(doc_id)
        return result
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        return {"status": "error", "message": str(e)}


@router.delete("/{doc_id}")
async def delete_document_endpoint(doc_id: int):
    """Delete a document."""
    try:
        delete_document(doc_id)
        return {"status": "success", "message": "Document deleted"}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return {"status": "error", "message": str(e)}
