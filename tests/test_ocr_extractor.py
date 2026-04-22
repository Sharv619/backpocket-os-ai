import os
from unittest.mock import patch

# Mock env vars
os.environ["POSTGRES_DB_URL"] = "postgresql://backpocket_user:backpocket_password@localhost:5432/backpocket_db"

from services.documents.extractor import extract_document_entities

@patch("services.documents.extractor.get_ollama_response")
def test_extractor(mock_ollama):
    mock_ollama.return_value = '''
    {
        "client_name": "Bunnings Warehouse",
        "amount": 245.50,
        "tax_amount": 22.31,
        "due_date": null,
        "received_date": "2026-04-21",
        "items": [
            {"description": "Makita Drill", "quantity": 1, "unit_cost": 199.00},
            {"description": "Screws 100pk", "quantity": 2, "unit_cost": 23.25}
        ],
        "category": "materials"
    }
    '''
    
    test_user_id = "11111111-1111-1111-1111-111111111111"
    
    result = extract_document_entities(
        ocr_text="BUNNINGS WAREHOUSE... MAKITA DRILL $199.00...",
        filename="bunnings_receipt.pdf",
        user_id=test_user_id
    )
    
    print(result)
    assert result["status"] == "success"
    assert result["client_name"] == "Bunnings Warehouse"

if __name__ == "__main__":
    test_extractor()
