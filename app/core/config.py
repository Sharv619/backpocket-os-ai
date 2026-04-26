import logging
import os
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


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
SCHEDULE_JOBS_DONE = set()  # To prevent double-running in the same hour

# Setup logging with UTF-8 support for emojis
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ruff: noqa: E402
import services.database as db

# Initialize the database BEFORE importing any service that depends on it.
# services/database.py seeds default categories at import time, so all tables
# must exist before that module (or anything that triggers it) is loaded.
db.init_db()

from services.google_sheets import (
    test_sheets_connection,
    log_activity,
    ensure_sheets_exist,
)
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
