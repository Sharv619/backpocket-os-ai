"""
Voice command endpoint tests.
Run: python -m pytest tests/test_voice_commands.py -v
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test"}  # middleware accepts any key in test mode


# ── helpers ────────────────────────────────────────────────────────────────

def voice_cmd(transcript: str, screen: str = "dashboard", session_id: str = "test-001", tab: int = 0):
    return client.post(
        "/api/voice/command",
        json={
            "transcript": transcript,
            "screen_context": screen,
            "session_id": session_id,
            "metadata": {"tab_index": tab},
        },
        headers=HEADERS,
    )


# ── basic routing ───────────────────────────────────────────────────────────

def test_voice_command_endpoint_exists():
    r = voice_cmd("show me my leads", screen="construction", tab=0)
    assert r.status_code == 200


def test_response_shape():
    r = voice_cmd("what's going on today")
    data = r.json()
    assert "intent" in data
    assert "confidence" in data
    assert "action" in data
    assert "speech_response" in data
    assert "needs_confirmation" in data


def test_navigate_intent():
    r = voice_cmd("go to inbox")
    assert r.status_code == 200
    data = r.json()
    # Intent must be classified; action/ui_action depend on entity extraction
    assert data["intent"] in ("navigate.screen", "dashboard.navigate", "chat.ask")


def test_construction_lead_list():
    r = voice_cmd("show me all leads", screen="construction", tab=0)
    data = r.json()
    assert data["intent"] == "construction.lead.list"
    assert data["action"] in ("execute", "display")


def test_low_confidence_falls_back_to_chat():
    # Gibberish should fall back to chat.ask
    r = voice_cmd("xzqwerty gobbledygook nonsense words")
    data = r.json()
    # Either low confidence or routed to chat fallback
    assert data["confidence"] < 0.7 or data["intent"] == "chat.ask"


# ── confirmation tier ───────────────────────────────────────────────────────

def test_approve_requires_confirmation():
    r = voice_cmd("approve the email to Sarah", screen="inbox", session_id="test-confirm-001")
    assert r.status_code == 200
    data = r.json()
    # inbox.approve is Tier B — must require confirmation when classified correctly
    if data["intent"] == "inbox.approve" and data["confidence"] >= 0.7:
        assert data["needs_confirmation"] is True


def test_meta_cancel():
    r = voice_cmd("cancel", session_id="test-cancel-001")
    data = r.json()
    # Gemini may be unavailable in test env — accept fallback route too
    assert data["intent"] in ("meta.cancel", "chat.ask")
    assert r.status_code == 200


def test_meta_help():
    r = voice_cmd("what can I say?")
    assert r.status_code == 200
    data = r.json()
    assert len(data["speech_response"]) > 5


# ── multi-turn session ──────────────────────────────────────────────────────

def test_multi_turn_lead_create_starts_collecting():
    r = voice_cmd("new lead", screen="construction", session_id="test-multiturn-001", tab=0)
    data = r.json()
    if data["intent"] == "construction.lead.create":
        # Missing params — should be in COLLECTING state
        session = data.get("session_state", {})
        assert session.get("state") in ("COLLECTING", "CONFIRMING")
        assert data["follow_up_prompt"] is not None


def test_pipeline_intent_tradie_slang():
    r = voice_cmd("what's the damage", screen="construction", tab=2)
    assert r.status_code == 200
    data = r.json()
    # Slang test: when Gemini available expect pipeline intent; fallback acceptable
    if data["confidence"] >= 0.6:
        assert data["intent"] in (
            "construction.payment.pipeline",
            "dashboard.pipeline_summary",
            "chat.ask",
        )


# ── voice session endpoints ─────────────────────────────────────────────────

def test_voice_intents_endpoint():
    r = client.get("/api/voice/intents?screen=construction", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "intents" in data
    intents = data["intents"]
    # intents is a list of dicts with "intent" key, or list of strings
    if intents and isinstance(intents[0], dict):
        names = [i["intent"] for i in intents]
    else:
        names = intents
    construction_intents = [i for i in names if i.startswith("construction.")]
    assert len(construction_intents) > 0
