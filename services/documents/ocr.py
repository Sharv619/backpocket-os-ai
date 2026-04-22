"""
BackPocket OS — Document OCR Pipeline
Extracts text from invoices, receipts, and photos.
Replaces the broken Paperless-ngx stack with a fast native implementation.
"""

import logging
from io import BytesIO
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from a standard text-based PDF."""
    if not PdfReader:
        logger.error("PyPDF2 is not installed. Cannot extract PDF text.")
        return ""
        
    try:
        reader = PdfReader(BytesIO(file_bytes))
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
                
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Failed to read PDF text: {e}")
        return ""


def extract_text_from_image(file_bytes: bytes) -> str:
    """Stub for image-based OCR (Tesseract / Google Vision)."""
    # For MVP, we pass images directly to Gemini Vision Pro instead of running
    # heavy local Tesseract binaries. We will return a prompt note here so 
    # the classifier knows to forward the image bytes to Gemini.
    return "[IMAGE_REQUIRES_VISION_MODEL]"


def process_document(file_bytes: bytes, filename: str, mime_type: str) -> dict:
    """
    Main entry point for document OCR pipeline.
    Determines document type and extracts text natively.
    """
    logger.info(f"Processing document: {filename} ({mime_type})")
    
    extracted_text = ""
    
    if "pdf" in mime_type.lower() or filename.lower().endswith(".pdf"):
        extracted_text = extract_text_from_pdf(file_bytes)
        
        # If PyPDF2 returns empty string on a PDF, it's likely a scanned/image PDF
        if not extracted_text:
            extracted_text = "[IMAGE_REQUIRES_VISION_MODEL]"
            
    elif "image" in mime_type.lower() or filename.lower().endswith((".png", ".jpg", ".jpeg")):
        extracted_text = extract_text_from_image(file_bytes)
    
    else:
        # Fallback text decoding for plain text/csv files
        try:
            extracted_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            extracted_text = "[UNSUPPORTED_FILE_FORMAT]"
            
    return {
        "filename": filename,
        "mime_type": mime_type,
        "content": extracted_text,
        "status": "success" if extracted_text and not extracted_text.startswith("[") else "needs_vision"
    }
