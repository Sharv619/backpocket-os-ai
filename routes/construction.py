from fastapi import APIRouter, Request, HTTPException
import asyncio
import functools
import logging
import os
import requests
import json
import re
from typing import Optional
from services.construction import get_construction_manager

router = APIRouter(prefix="/api/construction", tags=["construction"])
logger = logging.getLogger(__name__)


@router.post("/leads")
async def create_lead(data: dict):
    """Create a new lead from email extraction"""
    try:
        # Validate required fields
        required_fields = [
            "client_name",
            "email",
            "job_type",
            "location",
            "estimated_budget",
        ]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}",
            }

        manager = get_construction_manager()

        result = manager.create_lead(
            client_name=data.get("client_name") or "",
            email=data.get("email") or "",
            job_type=data.get("job_type") or "",
            location=data.get("location") or "",
            urgency=data.get("urgency", "medium"),
            budget=float(data.get("estimated_budget") or 0),
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/leads")
async def get_leads(status: str = None):
    """Get all leads, optionally filtered by status"""
    try:
        manager = get_construction_manager()
        leads = manager.get_leads(status=status)
        return {"status": "success", "count": len(leads), "leads": leads}
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: int):
    """Get single lead details"""
    try:
        manager = get_construction_manager()
        lead = manager.get_lead(lead_id)
        if not lead:
            return {"status": "error", "message": "Lead not found"}
        return {"status": "success", "lead": lead}
    except Exception as e:
        logger.error(f"Error fetching lead: {e}")
        return {"status": "error", "message": str(e)}


@router.patch("/leads/{lead_id}")
async def update_lead_status(lead_id: int, data: dict):
    """Update lead status"""
    try:
        manager = get_construction_manager()
        result = manager.update_lead_status(lead_id, data.get("status"))
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error updating lead: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/quotes")
async def create_quote(data: dict):
    """Create a quote for a lead"""
    try:
        # Validate required fields
        required_fields = ["lead_id"]
        missing = [f for f in required_fields if data.get(f) is None]
        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}",
            }

        manager = get_construction_manager()
        result = manager.create_quote(
            lead_id=int(data.get("lead_id") or 0),
            client_name=data.get("client_name", ""),
            job_type=data.get("job_type", ""),
            materials_cost=float(data.get("materials_cost", 0)),
            labor_cost=float(data.get("labor_cost", 0)),
            markup_percent=float(data.get("markup_percent", 20)),
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error creating quote: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/quotes")
async def get_quotes(status: str = None):
    """Get all quotes, optionally filtered by status"""
    try:
        manager = get_construction_manager()
        quotes = manager.get_quotes(status=status)
        return {"status": "success", "count": len(quotes), "quotes": quotes}
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/quotes/{quote_id}")
async def get_quote(quote_id: int):
    """Get single quote details"""
    try:
        manager = get_construction_manager()
        quote = manager.get_quote(quote_id)
        if not quote:
            return {"status": "error", "message": "Quote not found"}
        return {"status": "success", "quote": quote}
    except Exception as e:
        logger.error(f"Error fetching quote: {e}")
        return {"status": "error", "message": str(e)}


@router.patch("/quotes/{quote_id}")
async def update_quote_status(quote_id: int, data: dict):
    """Update quote status"""
    try:
        manager = get_construction_manager()
        result = manager.update_quote_status(quote_id, data.get("status"))
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error updating quote: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/pipeline")
async def get_pipeline():
    """Get quote pipeline summary"""
    try:
        manager = get_construction_manager()
        summary = manager.get_pipeline_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        logger.error(f"Error fetching pipeline: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/payments")
async def record_payment(data: dict):
    """Record a payment received"""
    try:
        if not data.get("quote_id") or not data.get("amount"):
            return {
                "status": "error",
                "message": "Missing required fields: quote_id and amount",
            }
        manager = get_construction_manager()
        result = manager.record_payment(
            quote_id=int(data.get("quote_id") or 0),
            amount=float(data.get("amount") or 0),
            client_name=data.get("client_name", ""),
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error recording payment: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/payments")
async def get_payments(quote_id: int = None):
    """Get all payments"""
    try:
        manager = get_construction_manager()
        payments = manager.get_payments(quote_id=quote_id)
        return {"status": "success", "count": len(payments), "payments": payments}
    except Exception as e:
        logger.error(f"Error fetching payments: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/leads/extract")
async def extract_lead_from_email(data: dict):
    """Extract lead data from email using Lead-to-Scope AI"""
    try:
        email_subject = data.get("subject", "")
        email_body = data.get("body", "")
        email_from = data.get("from", "")

        prompt = f"""Act as a specialized construction estimator. Analyze this email and extract the following as a JSON object:

{{
  "client_name": "(Full name from email or 'Unknown')",
  "job_type": "(e.g., Kitchen Reno, Deck, Emergency Repair)",
  "location": "(Street address if mentioned or empty string)",
  "pain_points": ["list", "of", "problems"],
  "scope_items": ["list", "of", "items"],
  "urgency": "(High/Medium/Low based on tone, default Medium)",
  "estimated_budget": (number or null)
}}

EMAIL:
From: {email_from}
Subject: {email_subject}
Body: {email_body}

Return ONLY the JSON object, no other text or markdown."""

        api_key = os.getenv("OPENROUTER_API_KEY")
        loop = asyncio.get_event_loop()
        _req = functools.partial(
            requests.post,
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "HTTP-Referer": "backpocket.ai"},
            json={"model": "openrouter/auto", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 300},
            timeout=15,
        )
        response = await loop.run_in_executor(None, _req)

        if response.status_code == 200:
            result = response.json()
            ai_response = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
            json_str = json_match.group(0) if json_match else ai_response
            extracted = json.loads(json_str)

            manager = get_construction_manager()
            lead_result = manager.create_lead(
                client_name=extracted.get("client_name", "Unknown"),
                email=email_from,
                job_type=extracted.get("job_type", "General"),
                location=extracted.get("location", ""),
                urgency=extracted.get("urgency", "medium").lower(),
                budget=extracted.get("estimated_budget"),
            )

            return {
                "status": "success",
                "lead_id": lead_result.get("lead_id"),
                "extracted_data": extracted,
            }
        else:
            return {
                "status": "error",
                "message": f"AI extraction failed: {response.status_code}",
            }
    except Exception as e:
        logger.error(f"Error extracting lead: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/quotes/{quote_id}/tradie-followup")
async def generate_tradie_followup(quote_id: int):
    """Generate friendly tradie follow-up message"""
    try:
        manager = get_construction_manager()
        quote = manager.get_quote(quote_id)
        if not quote:
            return {"status": "error", "message": "Quote not found"}

        prompt = f"""You are an AI Digital Twin for a professional contractor in Western Sydney.
Your tone is professional, reliable, and 'no-nonsense', but friendly.

Task: Draft a follow-up message for a quote sent to {quote["client_name"]}
regarding a {quote["job_type"]} job.

Constraints:
- Keep it under 60 words
- No corporate speak like 'per our previous correspondence'
- Use casual, respectful closings like 'Cheers' or 'Let me know'
- Include a subtle 'nudge' about schedule filling up
- Sound like a real person, not AI
- Include their specific job type
- One clear next step (call/email)

Generate ONLY the message text, nothing else."""

        api_key = os.getenv("OPENROUTER_API_KEY")
        loop = asyncio.get_event_loop()
        _req = functools.partial(
            requests.post,
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "HTTP-Referer": "backpocket.ai"},
            json={"model": "openrouter/auto", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 150},
            timeout=15,
        )
        response = await loop.run_in_executor(None, _req)

        if response.status_code == 200:
            result = response.json()
            message = (
                result.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": "Failed to generate message"}
    except Exception as e:
        logger.error(f"Error generating followup: {e}")
        return {"status": "error", "message": str(e)}
