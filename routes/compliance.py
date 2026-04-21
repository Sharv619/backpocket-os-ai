"""Compliance routes — ABN validation, GST verification."""
from fastapi import APIRouter
from pydantic import BaseModel
from services.abn_validator import validate_gst_amount, abn_info

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


class AbnRequest(BaseModel):
    abn: str


class GstRequest(BaseModel):
    subtotal_cents: int
    gst_cents: int


@router.post("/validate-abn")
async def check_abn(body: AbnRequest):
    """Validate an Australian Business Number (ABN) using ATO checksum."""
    return abn_info(body.abn)


@router.get("/validate-abn")
async def check_abn_get(abn: str):
    """Validate ABN via query param: GET /api/compliance/validate-abn?abn=51824753556"""
    return abn_info(abn)


@router.post("/validate-gst")
async def check_gst(body: GstRequest):
    """Verify GST amount is exactly 10% of subtotal (ATO requirement)."""
    valid = validate_gst_amount(body.subtotal_cents, body.gst_cents)
    expected = round(body.subtotal_cents * 0.1)
    return {
        "valid": valid,
        "subtotal_cents": body.subtotal_cents,
        "gst_cents": body.gst_cents,
        "expected_gst_cents": expected,
        "error": None if valid else f"GST should be {expected} cents (10%), got {body.gst_cents}",
    }
