import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def run_system_diagnostic() -> Dict[str, Any]:
    """Checks the health of Gmail, Sheets, Whapi, Gemini and Database."""
    from services.whapi import test_whapi_connection
    from services.google_sheets import test_sheets_connection
    from services.gmail import test_gmail_connection
    from services.gemini import test_gemini_connection
    import services.database as db

    results = {}

    # 1. WhatsApp
    try:
        results["whatsapp"] = test_whapi_connection()
    except Exception as e:
        results["whatsapp"] = {"status": "error", "message": str(e)}

    # 2. Google Sheets
    try:
        results["sheets"] = test_sheets_connection()
    except Exception as e:
        results["sheets"] = {"status": "error", "message": str(e)}

    # 3. Gmail
    try:
        results["gmail"] = test_gmail_connection()
    except Exception as e:
        results["gmail"] = {"status": "error", "message": str(e)}

    # 4. Gemini AI
    try:
        results["gemini"] = test_gemini_connection()
    except Exception as e:
        results["gemini"] = {"status": "error", "message": str(e)}

    # 5. Local Database
    try:
        pending = db.get_all_pending_refs()
        results["database"] = {"status": "success", "message": f"Connected ({len(pending)} pending items)"}
    except Exception as e:
        results["database"] = {"status": "error", "message": str(e)}

    # Overall Status
    healthy = all(r.get("status") == "success" for r in results.values())

    return {
        "status": "healthy" if healthy else "degraded",
        "details": results
    }
