import asyncio
import functools
import os
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/whatsapp-status")
async def get_whatsapp_status():
    try:
        from services.whapi import test_whapi_connection

        status = test_whapi_connection()
        return status
    except Exception as e:
        logger.error(f"WhatsApp status error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/api/whatsapp-test")
async def test_whatsapp_message():
    try:
        from services.whapi import send_whatsapp_message

        phone = os.getenv("FOUNDER_PHONE", "")
        if not phone:
            return {"status": "error", "message": "FOUNDER_PHONE not set"}
        result = send_whatsapp_message(
            phone, "BackPocket Twin: Test message successful! WhatsApp is connected."
        )
        return result
    except Exception as e:
        logger.error(f"WhatsApp test error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/api/client-master")
async def get_client_master():
    try:
        from services.google_sheets import get_sheets_service

        service = get_sheets_service()
        if not service:
            return {"status": "error", "message": "Google Sheets not connected"}

        spreadsheet_id = os.getenv("SPREADSHEET_ID")

        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_sheets = [
            s.get("properties", {}).get("title") for s in spreadsheet.get("sheets", [])
        ]

        sheet_names = [
            "Clients_Master",
            "BPS_Client_Master",
            "Client_Master",
            "Clients",
        ]
        range_found = None
        for sheet_name in sheet_names:
            if sheet_name in existing_sheets:
                range_found = f"{sheet_name}!A1:Z100"
                break

        if not range_found:
            return {
                "status": "error",
                "message": f"No client sheet found. Available: {existing_sheets}",
            }

        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_found)
            .execute()
        )

        values = result.get("values", [])
        if not values:
            return {"status": "empty", "clients": []}

        headers = values[0] if values else []
        clients = []
        for row in values[1:]:
            client = {}
            for i, header in enumerate(headers):
                client[header.lower().replace(" ", "_")] = (
                    row[i] if i < len(row) else ""
                )
            clients.append(client)

        return {"status": "success", "clients": clients, "count": len(clients)}
    except Exception as e:
        logger.error(f"Client master error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/api/style/scan-sent")
async def scan_sent_style(data: dict = {}):
    """Scan sent emails to learn writing style, update CHERRY_STYLE.txt."""
    try:
        from services.style_scanner import scan_sent_for_style

        token_file = data.get("token_file", "token.json")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            functools.partial(scan_sent_for_style, token_file=token_file),
        )
        return result
    except Exception as e:
        logger.error(f"Style scan error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/api/style/current")
async def get_current_style():
    """Return current CHERRY_STYLE.txt contents."""
    try:
        style_path = "docs/CHERRY_STYLE.txt"
        if not os.path.exists(style_path):
            return {"status": "not_found", "message": "Style file not found"}
        with open(style_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "success", "content": content, "file": style_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/api/drive/sync-to-rag")
async def sync_drive_to_rag(data: dict):
    try:
        from services.drive_integration import get_drive_integration

        drive = get_drive_integration()
        folder_id = data.get("folder_id", "")
        twin_type = data.get("twin_type", "admin")

        if not folder_id:
            return {"status": "error", "message": "folder_id is required"}

        result = drive.sync_folder_to_rag(folder_id, twin_type)

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error syncing Drive to RAG: {e}")
        return {"status": "error", "message": str(e)}
