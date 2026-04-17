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
    archive: bool = True


class LogRequest(BaseModel):
    content: str
    log_type: str = "session"


class AddClientRequest(BaseModel):
    ref_id: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    mobile: str = ""
    background_info: str = ""


class CoachAnalyzeRequest(BaseModel):
    ref_id: str


class SenderInstructionRequest(BaseModel):
    sender_email: str
    instructions: str
    category: str = ""


class HookRequest(BaseModel):
    name: str
    event: str
    action_type: str
    action_config: Optional[dict] = {}
    enabled: bool = True


class MobileApproveRequest(BaseModel):
    ref_id: str
    note: Optional[str] = None


class MobileChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class GBPPostRequest(BaseModel):
    job_description: str
    suburb: str


class TTSRequest(BaseModel):
    text: str
    voice: str = "male"
