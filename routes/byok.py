"""
SOVEREIGN ENGINE — Bring Your Own Key (BYOK)

Endpoints:
  POST   /api/settings/byok           — store encrypted API keys per user/session
  GET    /api/settings/byok-status    — which providers are configured (masked)
  DELETE /api/settings/byok/{provider} — clear a single provider key

Supported providers: openrouter, gemini, elevenlabs
Encryption: Fernet symmetric (services/crypto.py)
"""

import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

from services.byok import save_byok_key, get_byok_status, delete_byok_key, SUPPORTED_PROVIDERS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["byok"])


class BYOKRequest(BaseModel):
    provider: str
    api_key: str
    voice_id: Optional[str] = None  # ElevenLabs only


@router.post("/byok")
async def set_byok_key(body: BYOKRequest, request: Request):
    """Store user's own API key for a provider. Encrypted at rest."""
    if body.provider not in SUPPORTED_PROVIDERS:
        return {
            "status": "error",
            "message": f"Unknown provider. Supported: {', '.join(SUPPORTED_PROVIDERS)}",
        }
    user_id = getattr(request.state, "user_id", "default")
    try:
        save_byok_key(user_id, body.provider, body.api_key, extra=body.voice_id)
        return {
            "status": "success",
            "message": f"{body.provider} key saved. Your calls now use your own key.",
            "provider": body.provider,
            "sovereign": True,
        }
    except Exception as e:
        logger.error(f"BYOK save error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/byok-status")
async def byok_status(request: Request):
    """Return which providers have BYOK keys configured (never expose raw key)."""
    user_id = getattr(request.state, "user_id", "default")
    try:
        status = get_byok_status(user_id)
        return {"status": "success", "providers": status}
    except Exception as e:
        logger.error(f"BYOK status error: {e}")
        return {"status": "error", "message": str(e)}


@router.delete("/byok/{provider}")
async def clear_byok_key(provider: str, request: Request):
    """Remove a stored BYOK key. Reverts to server default key."""
    if provider not in SUPPORTED_PROVIDERS:
        return {"status": "error", "message": f"Unknown provider: {provider}"}
    user_id = getattr(request.state, "user_id", "default")
    try:
        delete_byok_key(user_id, provider)
        return {
            "status": "success",
            "message": f"{provider} key removed. Reverted to shared server key.",
            "provider": provider,
        }
    except Exception as e:
        logger.error(f"BYOK delete error: {e}")
        return {"status": "error", "message": str(e)}
