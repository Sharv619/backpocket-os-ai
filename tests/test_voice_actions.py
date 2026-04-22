import os
from unittest.mock import patch

# Mock env vars
os.environ["POSTGRES_DB_URL"] = "postgresql://backpocket_user:backpocket_password@localhost:5432/backpocket_db"

from services.voice_to_actions import process_site_visit_transcript

@patch("services.voice_to_actions.get_openrouter_response")
def test_pipeline(mock_openrouter):
    mock_openrouter.return_value = '''
    {
        "materials_list": ["5 bags cement", "2 rolls wire"],
        "subcontractors_list": ["Dave sparky"],
        "client_promises": ["fix gate next week"],
        "action_items": ["order supplies by Friday"]
    }
    '''
    
    # Test user
    test_user_id = "22222222-2222-2222-2222-222222222222"
    transcript = "I need 5 bags cement and 2 rolls wire. Call Dave sparky. Promised client to fix gate next week. order supplies by Friday."
    
    result = process_site_visit_transcript(transcript, test_user_id)
    print(result)

if __name__ == "__main__":
    test_pipeline()
