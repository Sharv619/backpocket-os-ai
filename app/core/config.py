import logging
from typing import Optional
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
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# ruff: noqa: E402
import services.database as db

# Initialize the database BEFORE importing any service that depends on it.
# services/database.py seeds default categories at import time, so all tables
# must exist before that module (or anything that triggers it) is loaded.
db.init_db()

