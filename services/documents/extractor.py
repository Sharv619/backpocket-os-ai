"""
BackPocket OS — Receipt & Invoice Extractor
Uses local Ollama models to parse raw OCR text into structured financial records.
"""

import json
import logging
from typing import Dict, Any

from services.gemini import get_ollama_response
from services.db_router import get_conn

logger = logging.getLogger(__name__)


def extract_document_entities(ocr_text: str, filename: str, user_id: str, quote_id: int | None = None) -> Dict[str, Any]:
    """
    Parses OCR text using a local Ollama model to extract vendor, date, amounts, and line items.
    Saves the result to the `payments` table.
    """
    prompt = f"""You are an expert accountant for a tradie business. 
Extract the structured financial data from this raw OCR text taken from a receipt or invoice. 
Return ONLY a valid JSON object matching the requested schema. Do not include any markdown formatting like ```json.

FILENAME: {filename}
OCR TEXT:
"{ocr_text}"

REQUIRED JSON SCHEMA:
{{
    "client_name": "string (the vendor or client name)",
    "amount": "number (the total amount)",
    "tax_amount": "number (GST or tax portion if present, else 0)",
    "due_date": "string (YYYY-MM-DD or null)",
    "received_date": "string (YYYY-MM-DD or null, use receipt date)",
    "items": [
        {{"description": "string", "quantity": 1, "unit_cost": "number"}}
    ],
    "category": "string (e.g. materials, fuel, tools, subcontractor, other)"
}}
"""
    
    # Call local AI (Ollama)
    response_text = get_ollama_response(
        prompt=prompt,
        json_mode=True
    )

    extracted_data = {
        "client_name": "Unknown Vendor",
        "amount": 0.0,
        "tax_amount": 0.0,
        "due_date": None,
        "received_date": None,
        "items": [],
        "category": "other"
    }

    if response_text:
        try:
            # Clean up potential markdown formatting
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(clean_text)
            
            # Map back to our structure
            for key in extracted_data.keys():
                if key in parsed_json:
                    extracted_data[key] = parsed_json[key]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse document JSON from Ollama: {e}\nResponse: {response_text}")
            return {"status": "error", "error": "AI returned invalid JSON."}

    # Save to DB
    try:
        conn = get_conn(user_id=user_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO payments 
                (user_id, quote_id, client_name, amount, due_date, received_date, status) 
                VALUES (%s, %s, %s, %s, %s, %s, 'completed')
                RETURNING id
                """,
                (
                    user_id, 
                    quote_id, 
                    extracted_data.get("client_name"), 
                    float(extracted_data.get("amount", 0)), 
                    extracted_data.get("due_date"), 
                    extracted_data.get("received_date")
                )
            )
            # Fetch the returned ID if supported (Postgres)
            res = cur.fetchone()
            inserted_id = res[0] if res else None
        conn.commit()
        
        extracted_data["payment_id"] = inserted_id
        extracted_data["status"] = "success"
        
    except Exception as e:
        logger.error(f"Database error saving payment from receipt: {e}")
        extracted_data["status"] = "error"
        extracted_data["error"] = str(e)

    return extracted_data
