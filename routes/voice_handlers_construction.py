"""
BackPocket OS — Voice Handlers: Construction (Leads, Quotes, Payments)
Handles all construction.lead.*, construction.quote.*, construction.payment.* intents.
"""

import logging
import httpx

from routes._voice_handlers import register_handler
from services.entity_resolver import resolve_entity, resolve_lead_by_id, resolve_quote_by_id
from services.construction import get_construction_manager

logger = logging.getLogger(__name__)

BASE = "http://127.0.0.1:8000"


# ── Site Visits ──────────────────────────────────────────────────────────────

@register_handler("construction.site_visit.log")
async def handle_site_visit_log(params: dict, screen_context: str, metadata: dict | None) -> dict:
    from services.voice_to_actions import process_site_visit_transcript
    from services.request_context import get_current_user_id
    
    transcript = params.get("transcript", metadata.get("raw_transcript", ""))
    if not transcript:
        return {"error": "What did you see on site?"}

    user_id = get_current_user_id() or "dev-user"
    quote_id = params.get("quote_id", params.get("lead_id"))
    
    if quote_id:
        try:
            quote_id = int(quote_id)
        except (ValueError, TypeError):
            quote_id = None
    
    # Process transcript using the new Pipeline
    extracted = process_site_visit_transcript(transcript, user_id=user_id, quote_id=quote_id)
    
    if extracted.get("status") == "success":
        mats = len(extracted.get("materials_list", []))
        subs = len(extracted.get("subcontractors_list", []))
        actions = len(extracted.get("action_items", []))
        promises = len(extracted.get("client_promises", []))
        
        summary_msg = f"Site visit logged! Found {mats} materials, {subs} subbies, {promises} promises, and {actions} actions."
        return {
            "status": "success",
            "materials_count": mats,
            "subcontractors_count": subs,
            "actions_count": actions,
            "promises_count": promises,
            "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True, "show_toast": summary_msg},
            "speech_response": summary_msg
        }
    
    return {"error": "Failed to log site visit. " + extracted.get("error", "")}

# ── Leads ────────────────────────────────────────────────────────────────────

@register_handler("construction.lead.create")
async def handle_lead_create(params: dict, screen_context: str, metadata: dict | None) -> dict:
    payload = {
        "client_name": params.get("client_name", ""),
        "email": params.get("email", ""),
        "job_type": params.get("job_type", ""),
        "location": params.get("location", ""),
        "urgency": params.get("urgency", "medium"),
        "estimated_budget": int(float(params.get("estimated_budget", 0))),
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{BASE}/api/construction/leads", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            lead_id = data.get("lead_id", data.get("id"))
            return {
                **payload,
                "lead_id": lead_id,
                "_entity": {"type": "lead", "id": lead_id, "client_name": payload["client_name"]},
                "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
            }
    return {"error": "Failed to create lead."}


@register_handler("construction.lead.list")
async def handle_lead_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE}/api/construction/leads")
        if resp.status_code == 200:
            leads = resp.json().get("leads", [])
            return {
                "count": len(leads),
                "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
            }
    return {"count": 0}


@register_handler("construction.lead.detail")
async def handle_lead_detail(params: dict, screen_context: str, metadata: dict | None) -> dict:
    lead_id = params.get("lead_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not lead_id and fuzzy:
        resolved = resolve_entity("lead", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            lead_id = resolved["entity"]["id"]
            return {
                **resolved["entity"],
                "_entity": resolved["entity"],
                "_ui_action": {"navigate_to": "construction", "tab_index": 0, "highlight_item": lead_id},
            }
        if resolved["match"] == "multiple":
            return {"error": "multiple_matches", "candidates": resolved["candidates"]}

    if lead_id:
        entity = resolve_lead_by_id(int(lead_id))
        if entity:
            return {**entity, "_entity": entity, "_ui_action": {"navigate_to": "construction", "tab_index": 0, "highlight_item": lead_id}}

    return {"error": "Couldn't find that lead."}


@register_handler("construction.lead.update")
async def handle_lead_update(params: dict, screen_context: str, metadata: dict | None) -> dict:
    lead_id = params.get("lead_id")
    status = params.get("status", "contacted")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not lead_id and fuzzy:
        resolved = resolve_entity("lead", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            lead_id = resolved["entity"]["id"]

    if not lead_id:
        return {"error": "Which lead?"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.patch(f"{BASE}/api/construction/leads/{lead_id}", json={"status": status})
        if resp.status_code == 200:
            entity = resolve_lead_by_id(int(lead_id))
            return {
                "client_name": entity.get("client_name", "") if entity else "",
                "status": status,
                "_entity": entity,
                "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
            }
    return {"error": "Failed to update lead."}


@register_handler("construction.lead.extract")
async def handle_lead_extract(params: dict, screen_context: str, metadata: dict | None) -> dict:
    email_ref = params.get("email_ref_id", params.get("ref_id", ""))

    email_data = {}
    if email_ref:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE}/api/mobile/pending")
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    if str(email_ref).lower() in (item.get("sender", "") + item.get("subject", "")).lower():
                        email_data = {
                            "from": item.get("sender", ""),
                            "subject": item.get("subject", ""),
                            "body": item.get("body", item.get("preview", "")),
                        }
                        break

    if not email_data:
        email_data = {"from": params.get("sender", ""), "subject": params.get("subject", ""), "body": params.get("body", "")}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{BASE}/api/construction/leads/extract", json=email_data)
        if resp.status_code == 200:
            data = resp.json()
            lead = data.get("lead", data)
            return {
                "client_name": lead.get("client_name", ""),
                "job_type": lead.get("job_type", ""),
                "location": lead.get("location", ""),
                "estimated_budget": lead.get("estimated_budget", 0),
                "_entity": {"type": "lead", "id": lead.get("lead_id"), "client_name": lead.get("client_name", "")},
                "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
            }
    return {"error": "Failed to extract lead from email."}


# ── Quotes ───────────────────────────────────────────────────────────────────

@register_handler("construction.quote.create")
async def handle_quote_create(params: dict, screen_context: str, metadata: dict | None) -> dict:
    payload = {
        "lead_id": int(params.get("lead_id", 0)),
        "materials_cost": float(params.get("materials_cost", 0)),
        "labor_cost": float(params.get("labor_cost", 0)),
        "markup_percent": float(params.get("markup_percent", 20)),
    }

    lead = resolve_lead_by_id(payload["lead_id"])
    if lead:
        payload["client_name"] = lead.get("client_name", "")
        payload["job_type"] = lead.get("job_type", "")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{BASE}/api/construction/quotes", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            total = (payload["materials_cost"] + payload["labor_cost"]) * (1 + payload["markup_percent"] / 100)
            quote_id = data.get("quote_id", data.get("id"))
            return {
                **payload,
                "total_amount": total,
                "quote_id": quote_id,
                "_entity": {"type": "quote", "id": quote_id, "client_name": payload.get("client_name", "")},
                "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
            }
    return {"error": "Failed to create quote."}


@register_handler("construction.quote.list")
async def handle_quote_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE}/api/construction/quotes")
        if resp.status_code == 200:
            quotes = resp.json().get("quotes", [])
            return {
                "count": len(quotes),
                "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
            }
    return {"count": 0}


@register_handler("construction.quote.detail")
async def handle_quote_detail(params: dict, screen_context: str, metadata: dict | None) -> dict:
    quote_id = params.get("quote_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            return {
                **resolved["entity"],
                "_entity": resolved["entity"],
                "_ui_action": {"navigate_to": "construction", "tab_index": 1, "highlight_item": resolved["entity"]["id"]},
            }
        if resolved["match"] == "multiple":
            return {"error": "multiple_matches", "candidates": resolved["candidates"]}

    if quote_id:
        entity = resolve_quote_by_id(int(quote_id))
        if entity:
            return {**entity, "_entity": entity, "_ui_action": {"navigate_to": "construction", "tab_index": 1, "highlight_item": quote_id}}

    return {"error": "Couldn't find that quote."}


@register_handler("construction.quote.update")
async def handle_quote_update(params: dict, screen_context: str, metadata: dict | None) -> dict:
    quote_id = params.get("quote_id")
    status = params.get("status", "sent")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            quote_id = resolved["entity"]["id"]

    if not quote_id:
        return {"error": "Which quote?"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.patch(f"{BASE}/api/construction/quotes/{quote_id}", json={"status": status})
        if resp.status_code == 200:
            entity = resolve_quote_by_id(int(quote_id))
            return {
                "client_name": entity.get("client_name", "") if entity else "",
                "status": status,
                "_entity": entity,
                "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
            }
    return {"error": "Failed to update quote."}


@register_handler("construction.quote.followup")
async def handle_quote_followup(params: dict, screen_context: str, metadata: dict | None) -> dict:
    quote_id = params.get("quote_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            quote_id = resolved["entity"]["id"]

    if not quote_id:
        return {"error": "Which quote should I follow up on?"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{BASE}/api/construction/quotes/{quote_id}/tradie-followup")
        if resp.status_code == 200:
            data = resp.json()
            return {
                "message": data.get("message", data.get("followup", "")),
                "_ui_action": {"navigate_to": "construction", "tab_index": 1},
            }
    return {"error": "Failed to generate follow-up."}


@register_handler("construction.quote.invoice")
async def handle_quote_invoice(params: dict, screen_context: str, metadata: dict | None) -> dict:
    quote_id = params.get("quote_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            quote_id = resolved["entity"]["id"]

    if not quote_id:
        return {"error": "Which quote should I invoice?"}

    # First, fetch the quote to get its details
    manager = get_construction_manager()
    quote = manager.get_quote(int(quote_id))
    if not quote:
        return {"error": f"Sorry, I couldn't find a quote with the ID {quote_id}."}

    # Auto-accept the quote before invoicing if using voice
    manager.update_quote_status(int(quote_id), "accepted")
    
    # Construct the invoice payload from the quote details
    invoice_items = [
        {"description": "Labor", "qty": 1, "rate": quote.get("labor_cost", 0), "gst": True},
        {"description": "Materials", "qty": 1, "rate": quote.get("materials_cost", 0), "gst": True},
    ]

    invoice_payload = {
        "client_name": quote.get("client_name"),
        "client_email": "", # Assuming email is not stored in quote, can be added later
        "items": invoice_items,
        "notes": f"Invoice for job: {quote.get('job_type')}",
        "quote_id": int(quote_id)
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{BASE}/api/invoice/generate", json=invoice_payload)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "invoice_url": data.get("url", ""),
                "total": data.get("total", 0),
                "_ui_action": {"navigate_to": "construction", "tab_index": 1},
            }
    return {"error": "Failed to generate invoice."}


# ── Payments ─────────────────────────────────────────────────────────────────

@register_handler("construction.payment.record")
async def handle_payment_record(params: dict, screen_context: str, metadata: dict | None) -> dict:
    quote_id = params.get("quote_id")
    amount = float(params.get("amount", 0))

    if not quote_id:
        return {"error": "Which quote is this payment for?"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{BASE}/api/construction/payments",
            json={"quote_id": int(quote_id), "amount": amount},
        )
        if resp.status_code == 200:
            quote = resolve_quote_by_id(int(quote_id))
            total = quote.get("total_amount", 0) if quote else 0
            return {
                "amount": amount,
                "client_name": quote.get("client_name", "") if quote else "",
                "remaining": max(0, total - amount),
                "_ui_action": {"navigate_to": "construction", "tab_index": 2, "refresh_data": True},
            }
    return {"error": "Failed to record payment."}


@register_handler("construction.payment.list")
async def handle_payment_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE}/api/construction/payments")
        if resp.status_code == 200:
            payments = resp.json().get("payments", [])
            return {
                "count": len(payments),
                "_ui_action": {"navigate_to": "construction", "tab_index": 2, "refresh_data": True},
            }
    return {"count": 0}


@register_handler("construction.payment.pipeline")
async def handle_payment_pipeline(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE}/api/construction/pipeline")
        if resp.status_code == 200:
            data = resp.json().get("data", resp.json())
            return {
                "total_revenue": data.get("total_revenue", 0),
                "outstanding": data.get("outstanding", data.get("total_pipeline_value", 0)),
                "_ui_action": {"navigate_to": "construction", "tab_index": 2},
            }
    return {"total_revenue": 0, "outstanding": 0}
