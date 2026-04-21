"""
BackPocket OS — Voice-to-Quote Routes
FastAPI endpoints for voice transcription and quote generation.
"""

import asyncio
import functools
import os
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Request
from pydantic import BaseModel
import requests

# ═══════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/voice", tags=["voice"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")

# ═══════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════


class QuoteDraftRequest(BaseModel):
    transcript: str


class QuoteDraft(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    items: list[dict] = []
    labor_hours: float = 0
    materials_cost: float = 0
    markup_percent: int = 20
    notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...), model: str = Form(default="tiny")
) -> dict:
    """
    Transcribe audio using faster-whisper on Oracle ARM.
    Returns: { "transcript": str }
    """
    # Save temp file
    content = await audio.read()

    try:
        # Try faster-whisper first (local) — run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        _req = functools.partial(
            requests.post,
            f"{OLLAMA_URL}/api/transcribe",
            files={"file": ("audio.m4a", content, "audio/m4a")},
            data={"model": model},
            timeout=60,
        )
        response = await loop.run_in_executor(None, _req)

        if response.status_code == 200:
            return response.json()

    except Exception as e:
        print(f"[WARN] Whisper failed: {e}")

    # Fallback: Use Gemini for basic transcription
    # (You'd integrate proper Whisper here)
    return {"transcript": "", "error": "Transcription service unavailable"}


@router.post("/quote-from-transcript")
async def quote_from_transcript(request: QuoteDraftRequest) -> dict:
    """
    Parse transcript into structured quote using Trinity model.
    """
    transcript = request.transcript

    # Use prompt engineering for Trinity
    prompt = _build_quote_prompt(transcript)

    try:
        # Call Ollama with Trinity model — run in executor to avoid blocking event loop
        import json
        loop = asyncio.get_event_loop()
        _req = functools.partial(
            requests.post,
            f"{OLLAMA_URL}/api/generate",
            json={"model": "gemma2:2b", "prompt": prompt, "format": "json", "stream": False},
            timeout=45,
        )
        response = await loop.run_in_executor(None, _req)

        if response.status_code == 200:
            result = response.json()
            try:
                quote_data = json.loads(result.get("response", "{}"))
                return {"quote_draft": quote_data}
            except Exception:
                pass
    except Exception:
        pass

    # Fallback
    return {
        "quote_draft": {
            "job_description": transcript[:200],
            "labor_hours": 2,
            "materials_cost": 0,
            "markup_percent": 20,
            "notes": "Needs manual review",
        }
    }


@router.post("/site-visit")
async def site_visit_transcript(request: QuoteDraftRequest, req: Request) -> dict:
    """
    Parse a site visit transcript to extract materials, subbies, and action items.
    Saves to the site_visits DB table.
    """
    from services.voice_to_actions import process_site_visit_transcript
    
    user_id = getattr(req.state, "user_id", "default_user")
    transcript = request.transcript
    
    if not transcript:
        return {"error": "No transcript provided"}

    extracted_data = process_site_visit_transcript(transcript, user_id=user_id)
    
    return {"status": extracted_data.get("status", "success"), "data": extracted_data}


def _build_quote_prompt(transcript: str) -> str:
    """Build prompt for quote extraction."""
    return f"""You are a construction quote parser. Extract quote details from this voice transcript.

TRANSCRIPT:
{transcript}

Extract these fields as JSON:
- client_name (string or null)
- client_email (string or null)
- job_description (string - what work needs doing)
- location (string - suburb/address)
- items (array of {{description, quantity, unit_cost}})
- labor_hours (number - estimated hours)
- materials_cost (number - materials total)
- markup_percent (number - default 20)
- notes (string or null)

Respond ONLY with valid JSON, no explanation."""
