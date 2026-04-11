import os
import base64
import logging
import sqlite3
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"
UPLOAD_DIR = "uploads"

# ── OpenRouter vision config ──────────────────────────────────────────────────
# Tried in order until one succeeds. All free-tier, all support image input.
#   1. gemma-3-27b  — best quality, 131k ctx, free (may rate-limit)
#   2. gemma-3-12b  — lighter, 32k ctx, free
#   3. nemotron-12b — NVIDIA, 128k ctx, free (image+video), good fallback
VISION_MODEL_PRIMARY = os.getenv(
    "OPENROUTER_VISION_MODEL", "google/gemma-3-27b-it:free"
)
VISION_MODELS = [
    VISION_MODEL_PRIMARY,
    "google/gemma-3-12b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
]
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Known valid image magic bytes
_IMAGE_MAGIC = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"GIF8": "gif",
    b"RIFF": "webp",  # RIFF....WEBP
}

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


def _call_openrouter_vision(image_b64: str, prompt: str, model: str) -> str:
    """Send a base64 image + prompt to OpenRouter vision model. Returns response text."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://backpocket.os",
        "X-Title": "BackPocket OS",
        "Content-Type": "application/json",
    }

    # OpenRouter vision format: content is a list with text + image_url parts
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 1500,
    }

    response = requests.post(
        OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=60
    )

    if response.status_code != 200:
        raise Exception(
            f"OpenRouter vision error {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]


def analyze_document(doc_id, custom_prompt: str | None = None):
    """Analyze a document image using OpenRouter vision (gemma-3-27b-it:free).
    Falls back to gemma-3-12b-it:free if the primary model fails.
    """
    doc = get_document(doc_id)
    if not doc:
        return {"status": "error", "message": "Document not found"}

    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found on disk"}

    # Non-image files (e.g. PDFs) — skip vision, return a helpful message
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        return {
            "status": "error",
            "message": f"Vision model requires an image file. Got: {ext}. "
            "Please upload a JPG or PNG.",
        }

    try:
        with open(file_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return {"status": "error", "message": f"Could not read file: {e}"}

    prompt = custom_prompt or (
        "You are a document analysis assistant for an Australian accounting firm.\n"
        "Analyse this document image and extract:\n"
        "1. Document type (invoice, receipt, contract, tax form, letter, other)\n"
        "2. Key information: dates, dollar amounts, ABN/ACN, names, addresses\n"
        "3. Any action items or deadlines visible\n"
        "4. A plain-English summary of what this document is about\n\n"
        "Be concise. If something is not visible, say 'not visible'."
    )

    ai_response = None
    used_model = None

    # Try models in order until one succeeds
    for model in VISION_MODELS:
        try:
            logger.info(f"Vision analysis: trying {model} for doc {doc_id}")
            ai_response = _call_openrouter_vision(image_b64, prompt, model)
            used_model = model
            logger.info(
                f"Vision analysis success with {model} ({len(ai_response)} chars)"
            )
            break
        except Exception as e:
            logger.warning(f"Vision model {model} failed: {e}. Trying next...")

    if not ai_response:
        return {
            "status": "error",
            "message": "All vision models failed. Check OPENROUTER_API_KEY.",
        }

    # Persist analysis to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET ai_analysis = ?, status = 'analyzed' WHERE id = ?",
        (ai_response, doc_id),
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "analysis": ai_response,
        "model_used": used_model,
        "document_id": doc_id,
    }


init_documents_table()
