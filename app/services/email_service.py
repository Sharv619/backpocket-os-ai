import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import services.database as db
from services.gmail import send_email
from services.gemini import (
    triage_email,
    draft_response,
    refine_draft,
    batch_triage_emails,
    pre_triage_rules,
)
from services.whapi import send_notification
from services.self_check import run_self_check, send_morning_pulse
from services.local_audit import run_self_audit


class ApproveRequest(BaseModel):
    ref_id: str


class ReviseRequest(BaseModel):
    ref_id: str
    comment: Optional[str] = None
    new_draft: Optional[str] = None
    feedback: Optional[str] = None


class SaveDraftRequest(BaseModel):
    ref_id: str
    draft_body: str
    feedback: Optional[str] = None


class ArchiveRequest(BaseModel):
    ref_id: str
    archive: bool = True  # Default to archive


# Global state trackers
LAST_PATROL_TIME = "Syncing..."
SEND_JOBS_DONE = set()  # To prevent double-running in the same hour

# Setup logging with UTF-8 support for emojis
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# Initialize the database BEFORE importing any service that depends on it.
# services/database.py seeds default categories at import time, so all tables
# must exist before that module (or anything that triggers it) is loaded.
db.init_db()

# Initialize session database on startup
try:
    from services.session_manager import init_session_db
    init_session_db()
    logger.info("Session DB initialized")
except Exception as e:
    logger.warning(f"Session DB init skipped: {e}")

# Ensure required directories exist
for _dir in ["static", "logs", "docs"]:
    if not os.path.exists(_dir):
        os.makedirs(_dir)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import route controllers
from controllers.admin_controller import router as admin_router
from controllers.voice_controller import router as voice_router
from controllers.crm_controller import router as construction_router
from controllers.email_controller import router as mobile_router
from controllers.document_controller import router as documents_router

# Include route controllers
app.include_router(admin_router)
app.include_router(voice_router)
app.include_router(construction_router)
app.include_router(mobile_router)
app.include_router(documents_router)