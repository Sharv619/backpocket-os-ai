import asyncio
import os
from unittest.mock import patch, MagicMock

# Mock env vars
os.environ["POSTGRES_DB_URL"] = "postgresql://backpocket_user:backpocket_password@localhost:5432/backpocket_db"

from routes.voice_commands import VoiceCommandRequest, voice_command
from services.voice_to_actions import process_site_visit_transcript

@patch("services.voice_to_actions.process_site_visit_transcript")
@patch("routes.voice_commands.classify_intent")
async def test_end_to_end_site_visit(mock_classify, mock_process):
    # Mock classification to bypass Gemini
    mock_classify.return_value = {
        "intent": "construction.site_visit.log",
        "confidence": 0.95,
        "entities": {}
    }
    
    # Mock processing
    mock_process.return_value = {
        "status": "success",
        "materials_list": ["5 bags cement", "2 rolls wire"],
        "subcontractors_list": ["Dave sparky"],
        "client_promises": ["fix gate next week"],
        "action_items": ["order supplies by Friday"],
        "site_visit_id": 99
    }
    
    req = VoiceCommandRequest(
        transcript="I need 5 bags cement and 2 rolls wire. Call Dave sparky. Promised client to fix gate next week. order supplies by Friday.",
        screen_context="construction",
        session_id="test_session_123"
    )
    
    res = await voice_command(req)
    print(res)

if __name__ == "__main__":
    asyncio.run(test_end_to_end_site_visit())
