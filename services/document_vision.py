import os
import base64
import logging
import sqlite3
import uuid
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"
UPLOAD_DIR = "uploads"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "moondream")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def init_documents_table():
    """Create documents table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT,
            file_path TEXT NOT NULL,
            file_type TEXT,
            category TEXT DEFAULT 'other',
            ai_analysis TEXT,
            extracted_data TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_document(file_bytes, original_filename, category="other"):
    """Save uploaded file and return document ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ext = os.path.splitext(original_filename)[1].lower()
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    cursor.execute(
        """
        INSERT INTO documents (filename, original_name, file_path, file_type, category, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (unique_name, original_filename, file_path, ext, category, "pending"),
    )

    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return doc_id


def get_all_documents():
    """Get all documents."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id):
    """Get single document by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_document(doc_id):
    """Delete document and file."""
    doc = get_document(doc_id)
    if doc and os.path.exists(doc["file_path"]):
        os.remove(doc["file_path"])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return True


def analyze_document(doc_id):
    """Analyze document using Moondream vision model."""
    doc = get_document(doc_id)
    if not doc:
        return {"status": "error", "message": "Document not found"}

    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}

    try:
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        import requests

        ollama_url = f"{OLLAMA_BASE_URL}/api/chat"

        prompt = """You are a document analysis assistant. Analyze this image and extract:
1. Document type (invoice, receipt, contract, letter, form, other)
2. Key information (dates, amounts, names, addresses)
3. Any important text or numbers
4. Brief summary of what's in the document

Return as JSON with keys: document_type, key_info, important_text, summary"""

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt, "images": [image_data]}],
            "stream": False,
        }

        response = requests.post(ollama_url, json=payload, timeout=180)

        logger.info(f"Ollama response status: {response.status_code}")
        logger.info(f"Ollama response body: {response.text[:500]}")

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("message", {}).get("content", "")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE documents 
                SET ai_analysis = ?, status = 'analyzed', extracted_data = ?
                WHERE id = ?
            """,
                (ai_response, "{}", doc_id),
            )
            conn.commit()
            conn.close()

            return {"status": "success", "analysis": ai_response}
        else:
            return {
                "status": "error",
                "message": f"Ollama error: {response.status_code}",
            }

    except Exception as e:
        logger.error(f"Document analysis error: {e}")
        return {"status": "error", "message": str(e)}


init_documents_table()
