"""
Voice-to-Action Pipeline
Extracts structured lists (Materials, Subcontractors, Actions) from a site visit transcript
and saves them to the PostgreSQL/SQLite databases via db_router.
"""

import json
import logging
from typing import Dict, Any

from services.gemini import get_openrouter_response
from services.db_router import get_conn

logger = logging.getLogger(__name__)


def process_site_visit_transcript(transcript: str, user_id: str, quote_id: int | None = None) -> Dict[str, Any]:
    """
    Parses a raw voice transcript from a site visit to extract actionable lists
    and saves them directly to the `site_visits` table.
    """
    prompt = f"""You are an AI assistant for a tradie. Analyze this site visit voice transcript and extract the following lists. 
Return ONLY a valid JSON object matching the requested schema. Do not include any markdown formatting like ```json.

TRANSCRIPT:
"{transcript}"

REQUIRED JSON SCHEMA:
{{
    "materials_list": ["item 1", "item 2"],
    "subcontractors_list": ["person/trade 1", "person/trade 2"],
    "client_promises": ["promise 1"],
    "action_items": ["action 1"]
}}

If a list is empty, return an empty array [].
"""
    
    # Call AI
    response_text = get_openrouter_response(
        prompt=prompt,
        model="openrouter/auto",
        sys_prompt="You are a data extraction bot. Output only raw JSON.",
        user_id=user_id
    )

    extracted_data = {
        "materials_list": [],
        "subcontractors_list": [],
        "client_promises": [],
        "action_items": []
    }

    if response_text:
        try:
            # Clean up potential markdown formatting
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(clean_text)
            
            # Map back to our structure ensuring lists
            for key in extracted_data.keys():
                if key in parsed_json and isinstance(parsed_json[key], list):
                    extracted_data[key] = parsed_json[key]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse site visit JSON from AI: {e}\nResponse: {response_text}")

    # Convert lists to newline-separated strings for database storage
    materials_str = "\n".join(f"- {i}" for i in extracted_data["materials_list"])
    subs_str = "\n".join(f"- {i}" for i in extracted_data["subcontractors_list"])
    promises_str = "\n".join(f"- {i}" for i in extracted_data["client_promises"])
    actions_str = "\n".join(f"- {i}" for i in extracted_data["action_items"])

    # Save to DB
    try:
        conn = get_conn(user_id=user_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO site_visits 
                (user_id, quote_id, visit_date, transcript, materials_list, subcontractors_list, client_promises, action_items) 
                VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (user_id, quote_id, transcript, materials_str, subs_str, promises_str, actions_str)
            )
            # Fetch the returned ID if supported (Postgres)
            res = cur.fetchone()
            inserted_id = res[0] if res else None
        conn.commit()
        
        extracted_data["site_visit_id"] = inserted_id
        extracted_data["status"] = "success"
        
    except Exception as e:
        logger.error(f"Database error saving site visit: {e}")
        extracted_data["status"] = "error"
        extracted_data["error"] = str(e)

    return extracted_data
