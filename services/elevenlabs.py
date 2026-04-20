"""
ElevenLabs TTS service — eleven_turbo_v2_5 model, low-latency MP3.

Env vars:
  ELEVENLABS_API_KEY   — required
  ELEVENLABS_VOICE_ID  — optional, defaults to Adam (pNInz6obpgDQGcFmaJgB)
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
BASE_URL = "https://api.elevenlabs.io/v1"

# Voices — good tradie-sounding voices
VOICES = {
    "male":   os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"),  # Adam
    "female": "21m00Tcm4TlvDq8ikWAM",  # Rachel
}

# eleven_turbo_v2_5: ~400ms latency, multilingual, best for real-time UX
MODEL = "eleven_turbo_v2_5"


def is_configured() -> bool:
    return bool(API_KEY) and API_KEY != "your_elevenlabs_api_key_here"


async def synthesize(text: str, voice: str = "male") -> bytes:
    """Return MP3 bytes for the given text. Raises on API error."""
    if not is_configured():
        raise RuntimeError("ELEVENLABS_API_KEY not set")

    voice_id = VOICES.get(voice, VOICES["male"])

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{BASE_URL}/text-to-speech/{voice_id}",
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": API_KEY,
            },
            json={
                "text": text,
                "model_id": MODEL,
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.80,
                    "style": 0.0,
                    "use_speaker_boost": True,
                },
            },
        )

    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs {resp.status_code}: {resp.text[:200]}")

    return resp.content


def list_voices_url() -> str:
    return f"{BASE_URL}/voices"
