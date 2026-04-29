import os
import base64
import logging
import sqlite3
import uuid
import requests
import ollama
import json
from dotenv import load_dotenv

load_dotenv()

OLLAMA_VISION_MODEL = "moondream"

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"
TEMP_PATH = os.path.join(os.getcwd(), "temp_uploads")

# ── OpenRouter vision config ──────────────────────────────────────────────────
# Vision models tried in order until one succeeds.
#   1. gemini-2.5-flash-image — best free vision, fast
VISION_MODEL_PRIMARY = os.getenv(
    "OPENROUTER_VISION_MODEL", "google/gemini-2.5-flash-image"
)
VISION_MODELS = [
    VISION_MODEL_PRIMARY,
    "google/gemini-2.5-flash-image",
]
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Paperless-ngx OCR config ─────────────────────────────────────────────────
PAPERLESS_URL = os.getenv("PAPERLESS_URL", "http://localhost:8010")
PAPERLESS_TOKEN = os.getenv("PAPERLESS_TOKEN", "")


def _ocr_via_paperless(file_path: str, timeout: int = 120) -> str | None:
    """Upload image to Paperless-ngx, wait for OCR, return extracted text."""
    if not PAPERLESS_TOKEN:
        logger.debug("PAPERLESS_TOKEN not set — skipping Paperless OCR")
        return None
    headers = {"Authorization": f"Token {PAPERLESS_TOKEN}"}
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{PAPERLESS_URL}/api/documents/post_document/",
                headers=headers,
                files={"document": f},
                timeout=30,
            )
        if resp.status_code not in (200, 202):
            logger.warning(f"Paperless upload failed: {resp.status_code}")
            return None
        raw = resp.json()
        task_id = raw if isinstance(raw, str) else raw.get("task_id", "")
        logger.info(f"Paperless OCR task: {task_id}")

        import time
        for i in range(timeout // 3):
            time.sleep(3)
            task_resp = requests.get(
                f"{PAPERLESS_URL}/api/tasks/",
                headers=headers, timeout=10,
            )
            if task_resp.status_code != 200:
                continue
            all_tasks = task_resp.json()
            results = all_tasks if isinstance(all_tasks, list) else all_tasks.get("results", [])
            for t in results:
                if t.get("task_id") != task_id:
                    continue
                if t.get("status") == "SUCCESS" and t.get("related_document"):
                    doc_id = t["related_document"]
                    doc_resp = requests.get(
                        f"{PAPERLESS_URL}/api/documents/{doc_id}/",
                        headers=headers, timeout=10,
                    )
                    if doc_resp.status_code == 200:
                        content = doc_resp.json().get("content", "")
                        if content.strip():
                            logger.info(f"Paperless OCR success: {len(content)} chars")
                            return content
                    return None
                elif t.get("status") == "FAILURE":
                    logger.warning(f"Paperless OCR task failed: {t.get('result')}")
                    return None
                elif t.get("status") in ("STARTED", "PENDING"):
                    if i % 5 == 0:
                        logger.info(f"Paperless OCR still processing... ({i*3}s)")
                    break
        logger.warning("Paperless OCR timed out after 120s")
        return None
    except Exception as e:
        logger.warning(f"Paperless OCR error: {e}")
        return None


# Known valid image magic bytes
_IMAGE_MAGIC = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"GIF8": "gif",
    b"RIFF": "webp",  # RIFF....WEBP
}

os.makedirs(TEMP_PATH, exist_ok=True)


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
    file_path = os.path.join(TEMP_PATH, unique_name)

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
        "max_tokens": 512,
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


import asyncio

# Existing imports retained

def _store_extracted_entities(doc_id: int, entities_json: str) -> bool:
    """Store JSON of extracted construction entities into the documents table.
    Returns True on success, False otherwise.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET extracted_data = ? WHERE id = ?",
            (entities_json, doc_id),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error saving extracted entities for doc {doc_id}: {e}")
        return False

async def analyze_document_async(doc_id: int, custom_prompt: str | None = None) -> dict:
    """Async wrapper for document analysis.
    Executes the heavy vision work in a thread to keep the FastAPI event loop responsive.
    """
    return await asyncio.to_thread(analyze_document, doc_id, custom_prompt)

def _construction_entity_prompt() -> str:
    """Prompt that asks the vision model to extract construction-specific entities.
    The system prompt explicitly bans returning raw PII (names, phone numbers).
    """
    return (
        "You are an AI assistant for a construction workflow system. "
        "From the supplied image, extract ONLY the following fields as a JSON object: "
        "{\"job_type\": string, \"site_address\": string, \"measurements\": {\"length\": number, \"width\": number, \"height\": number}}. "
        "If any field is not visible, set its value to null. Do NOT include any personal identifying information such as client names or phone numbers in the output."
    )

# ---------------------------------------------------------------------------
# Updated main analysis function – now also extracts construction entities when applicable.
# ---------------------------------------------------------------------------

def analyze_document(doc_id, custom_prompt: str | None = None):
    """Analyze a document image using vision models and extract construction entities.
    
    This function now also updates the workflow stage to 3 (Onsite Inspection) when entity extraction succeeds.
    Returns a dict with status, analysis, model_used, and optional extracted_entities.
    """
    import services.database as db
    doc = get_document(doc_id)
    if not doc:
        return {"status": "error", "message": "Document not found"}

    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found on disk"}

    # Validate image type
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        return {
            "status": "error",
            "message": f"Vision model requires an image file. Got: {ext}. Please upload a JPG or PNG.",
        }

    # Load image bytes
    try:
        with open(file_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return {"status": "error", "message": f"Could not read file: {e}"}

    # Choose prompt – allow caller override or default
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

    # ---------------------------------------------------------------------
    # Vision cascade: Paperless OCR → Ollama moondream → OpenRouter → RAG
    # ---------------------------------------------------------------------

    # Layer 1: Paperless-ngx OCR (fast, local, no GPU needed)
    if not ai_response:
        ocr_text = _ocr_via_paperless(file_path)
        if ocr_text:
            ai_response = f"[Paperless OCR]\n{ocr_text.strip()}"
            used_model = "paperless_ocr"

    # Layer 2: Ollama moondream (local vision, needs GPU/CPU time)
    if not ai_response:
        try:
            logger.info(f"Vision analysis: trying {OLLAMA_VISION_MODEL} for doc {doc_id}")
            response = ollama.chat(
                model=OLLAMA_VISION_MODEL,
                messages=[{"role": "user", "content": prompt, "images": [image_b64]}],
            )
            ai_response = response["message"]["content"]
            used_model = f"ollama/{OLLAMA_VISION_MODEL}"
            logger.info(f"Vision analysis success with {OLLAMA_VISION_MODEL} ({len(ai_response)} chars)")
        except Exception as e:
            logger.warning(f"Ollama vision failed: {e}")

    # Layer 3: OpenRouter cloud vision (costs money)
    if not ai_response:
        for model in VISION_MODELS:
            try:
                ai_response = _call_openrouter_vision(image_b64, prompt, model)
                used_model = f"openrouter/{model}"
                break
            except Exception as e2:
                logger.warning(f"OpenRouter vision {model} failed: {e2}")

    # Layer 4: RAG fallback
    if not ai_response:
            logger.warning(f"[VISION] All models failed for doc {doc_id}. Attempting RAG fallback.")
            try:
                from services.agentic_rag import get_agentic_rag
                rag = get_agentic_rag()
                rag_context = rag.get_context_for_email(
                    {"snippet": f"Document analysis request for doc_id={doc_id}", "subject": "document"},
                    tier=2,
                )
                return {
                    "status": "rag_fallback",
                    "source": "chromadb_local",
                    "analysis": rag_context,
                    "document_id": doc_id,
                    "message": "Vision models unavailable. Returned local RAG context instead.",
                }
            except Exception as rag_err:
                logger.error(f"[VISION] RAG fallback also failed: {rag_err}")
                return {"status": "error", "message": "All vision models failed and RAG fallback unavailable."}

    # ---------------------------------------------------------------------
    # Store primary analysis result.
    # ---------------------------------------------------------------------
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET ai_analysis = ?, status = 'analyzed' WHERE id = ?",
        (ai_response, doc_id),
    )
    conn.commit()
    conn.close()

    # ---------------------------------------------------------------------
    # Optional second pass: ask for construction entity extraction.
    # This result is stored in the extracted_data column as JSON.
    # If extraction succeeds, advance workflow_stage to 3 (Onsite Inspection).
    # ---------------------------------------------------------------------
    try:
        entity_prompt = _construction_entity_prompt()
        entity_response = None
        if used_model == "paperless_ocr":
            from services.gemini import get_gemini_client
            client = get_gemini_client()
            if client:
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{entity_prompt}\n\nDocument text:\n{ai_response}",
                    config={"response_mime_type": "application/json"},
                )
                entity_response = resp.text if resp and resp.text else None
        elif used_model.startswith("ollama"):
            response = ollama.chat(
                model=OLLAMA_VISION_MODEL,
                messages=[{"role": "user", "content": entity_prompt, "images": [image_b64]}],
            )
            entity_response = response["message"]["content"]
        else:
            entity_response = _call_openrouter_vision(image_b64, entity_prompt, used_model.split('/')[-1])
        # Ensure JSON validity then store.
        try:
            json.loads(entity_response)
            _store_extracted_entities(doc_id, entity_response)
            # Advance workflow stage to 3 (Onsite Inspection)
            try:
                import services.database as db
                db.update_workflow_stage(str(doc_id), "3")
                logger.info(f"Workflow stage for doc {doc_id} advanced to 3 after entity extraction.")
            except Exception as we_err:
                logger.warning(f"Failed to update workflow stage for doc {doc_id}: {we_err}")
        except Exception:
            logger.warning(f"Entity extraction did not return valid JSON for doc {doc_id}")
    except Exception as e:
        logger.warning(f"Construction entity extraction failed for doc {doc_id}: {e}")
    return {
        "status": "success",
        "analysis": ai_response,
        "model_used": used_model,
        "document_id": doc_id,
    }


init_documents_table()


# ── Building material / damage assessment prompts ─────────────────────────────

MATERIAL_VISION_PROMPT = """You are an expert building inspector assistant helping an Australian tradie assess a job site photo.

Analyse this image and return a JSON object with EXACTLY these fields:
{
  "material_type": "<primary material visible: brick/timber/concrete/render/tile/metal/other>",
  "condition_score": <integer 1-10 where 10=new, 1=failed>,
  "damage_visible": <true/false>,
  "damage_types": ["<list of: crack/water_damage/rot/rust/spalling/mould/other>"],
  "urgency": "<immediate/soon/routine/none>",
  "estimated_hours": <integer — rough labour hours to fix>,
  "notes": "<one sentence plain-English assessment for the tradie>"
}

Return ONLY the JSON. No markdown, no extra text."""

DAMAGE_ASSESSMENT_PROMPT = """You are a structural damage assessor helping an Australian tradie quote a repair job.

Look at this photo and return a JSON object with EXACTLY these fields:
{
  "structural_concern": <true/false>,
  "crack_severity": "<none/hairline/moderate/severe>",
  "water_ingress": <true/false>,
  "affected_area_sqm": <float estimate or null if cannot determine>,
  "repair_complexity": "<simple/moderate/complex>",
  "recommended_action": "<one sentence: what the tradie should do first>",
  "safety_risk": <true/false>
}

Return ONLY the JSON. No markdown, no extra text."""


def analyze_text_content(doc_id: int, text_content: str, custom_prompt: str | None = None) -> dict:
    """Analyze pre-extracted text content using the configured TwinEngine AI provider."""
    prompt = custom_prompt or (
        "You are a document analysis assistant for an Australian accounting firm.\n"
        f"A document has been processed via OCR and the following text was extracted:\n\n---\n{text_content}\n---\n\n"
        "Please analyze this text and extract:\n"
        "1. Document type (invoice, receipt, contract, tax form, letter, other)\n"
        "2. Key information: dates, dollar amounts, ABN/ACN, names, addresses\n"
        "3. Any action items or deadlines visible\n"
        "4. A plain-English summary of what this document is about\n\n"
        "Be concise. If something is not visible, say 'not visible'."
    )
    
    try:
        from services.twin_engine import TwinEngine
        engine = TwinEngine()
        ai_response = engine.get_completion(prompt)

        # Store the AI analysis result
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
            "model_used": f"provider/{engine.provider.__class__.__name__}",
            "document_id": doc_id,
        }
    except Exception as e:
        logger.error(f"Text analysis failed for doc {doc_id}: {e}")
        return {"status": "error", "message": str(e)}

def analyze_building_image(image_b64: str, analysis_type: str = "material") -> dict:
    """
    Analyse a building/site photo for materials or structural damage.
    analysis_type: 'material' | 'damage'
    Returns structured dict parsed from AI JSON response.
    """
    import json as _json

    prompt = MATERIAL_VISION_PROMPT if analysis_type == "material" else DAMAGE_ASSESSMENT_PROMPT

    raw = None
    for model in VISION_MODELS:
        try:
            raw = _call_openrouter_vision(image_b64, prompt, model)
            if raw:
                break
        except Exception as e:
            logger.warning(f"Vision model {model} failed: {e}")

    if not raw:
        return {"error": "All vision models failed", "analysis_type": analysis_type}

    try:
        cleaned = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = _json.loads(cleaned)
        result["analysis_type"] = analysis_type
        return result
    except _json.JSONDecodeError:
        return {"analysis_type": analysis_type, "raw": raw, "parse_error": "Could not parse JSON from AI response"}

def vision_query_gemini(image_bytes: bytes, user_query: str) -> dict:
    """
    Prompt 2: Multimodal Photo-to-Query logic.
    Uses Gemini 2.5 Flash for material estimation/measurements.
    """
    from services.gemini import get_gemini_client
    import PIL.Image
    import io
    import json as _json

    client = get_gemini_client()
    if not client:
        return {"error": "Gemini client not initialized"}

    try:
        img = PIL.Image.open(io.BytesIO(image_bytes))
        
        prompt = f"""
        User Query: {user_query}
        
        Analyze this site photo and answer the user's query with a focus on construction accuracy.
        You MUST return a strict JSON structure containing:
        {{
          "estimated_measurements": {{ "key": "value" }}, 
          "required_materials": ["item1", "item2"], 
          "confidence_score": float (0.0 to 1.0),
          "analysis": "brief explanation"
        }}
        Return ONLY the JSON.
        """
        
        # Using the new google-genai SDK format
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, img],
            config={"response_mime_type": "application/json"}
        )
        
        if response and response.text:
            return _json.loads(response.text)
        return {"error": "Empty response from Gemini"}
    except Exception as e:
        logger.error(f"vision_query_gemini error: {e}")
        return {"error": str(e)}
