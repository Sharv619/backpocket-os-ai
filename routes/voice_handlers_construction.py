"""
BackPocket OS — Voice Handlers: Construction (Leads, Quotes, Payments)
Handles all construction.lead.*, construction.quote.*, construction.payment.* intents.
"""

from datetime import datetime, timedelta
import logging

from routes._voice_handlers import register_handler
from routes.construction import extract_lead_from_email
from services.construction import get_construction_manager
from services.pending_emails import find_pending_email
from services.entity_resolver import resolve_entity, resolve_lead_by_id, resolve_quote_by_id
from services.invoice_engine import generate_invoice_pdf, next_invoice_number

logger = logging.getLogger(__name__)


# ── Leads ────────────────────────────────────────────────────────────────────

@register_handler("construction.lead.create")
async def handle_lead_create(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    payload = {
        "client_name": params.get("client_name", ""),
        "email": params.get("email", ""),
        "job_type": params.get("job_type", ""),
        "location": params.get("location", ""),
        "urgency": params.get("urgency", "medium"),
        "estimated_budget": float(params.get("estimated_budget", 0) or 0),
        "client_action_id": (metadata or {}).get("client_action_id"),
    }
    result = manager.create_lead(
        client_name=payload["client_name"],
        email=payload["email"],
        job_type=payload["job_type"],
        location=payload["location"],
        urgency=payload["urgency"],
        budget=payload["estimated_budget"],
        client_action_id=payload["client_action_id"],
    )
    lead_id = result.get("lead_id")
    return {
        **payload,
        "lead_id": lead_id,
        "email": result.get("email", payload["email"]),
        "status": result.get("status", "created"),
        "_entity": {"type": "lead", "id": lead_id, "client_name": payload["client_name"]},
        "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
    }


@register_handler("construction.lead.list")
async def handle_lead_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    leads = manager.get_leads(status=params.get("status"))
    return {
        "count": len(leads),
        "leads": leads[:10],
        "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
    }


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
    manager = get_construction_manager()
    lead_id = params.get("lead_id")
    status = params.get("status", "contacted")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not lead_id and fuzzy:
        resolved = resolve_entity("lead", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            lead_id = resolved["entity"]["id"]

    if not lead_id:
        return {"error": "Which lead?"}

    manager.update_lead_status(int(lead_id), status)
    entity = resolve_lead_by_id(int(lead_id))
    return {
        "client_name": entity.get("client_name", "") if entity else "",
        "status": status,
        "_entity": entity,
        "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
    }


@register_handler("construction.lead.extract")
async def handle_lead_extract(params: dict, screen_context: str, metadata: dict | None) -> dict:
    email_ref = params.get("email_ref_id", params.get("ref_id", ""))

    email_data = {}
    if email_ref:
        item = find_pending_email(str(email_ref))
        if item:
            email_data = {
                "from": item.get("sender", ""),
                "subject": item.get("subject", ""),
                "body": item.get("body", item.get("preview", "")),
            }

    if not email_data:
        email_data = {
            "from": params.get("sender", ""),
            "subject": params.get("subject", ""),
            "body": params.get("body", ""),
        }

    data = await extract_lead_from_email(email_data)
    if data.get("status") == "success":
        lead = data.get("extracted_data", {})
        return {
            "lead_id": data.get("lead_id"),
            "client_name": lead.get("client_name", ""),
            "job_type": lead.get("job_type", ""),
            "location": lead.get("location", ""),
            "estimated_budget": lead.get("estimated_budget", 0),
            "_entity": {
                "type": "lead",
                "id": data.get("lead_id"),
                "client_name": lead.get("client_name", ""),
            },
            "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
        }
    return {"error": "Failed to extract lead from email."}


# ── Quotes ───────────────────────────────────────────────────────────────────

@register_handler("construction.quote.create")
async def handle_quote_create(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    lead_id = params.get("lead_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))
    if not lead_id and fuzzy:
        resolved = resolve_entity("lead", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            lead_id = resolved["entity"]["id"]

    if not lead_id:
        return {"error": "Which lead is this quote for?"}

    payload = {
        "lead_id": int(lead_id),
        "materials_cost": float(params.get("materials_cost", 0)),
        "labor_cost": float(params.get("labor_cost", 0)),
        "markup_percent": float(params.get("markup_percent", 20)),
        "client_action_id": (metadata or {}).get("client_action_id"),
    }

    lead = resolve_lead_by_id(payload["lead_id"])
    if lead:
        payload["client_name"] = lead.get("client_name", "")
        payload["job_type"] = lead.get("job_type", "")

    result = manager.create_quote(
        lead_id=payload["lead_id"],
        client_name=payload.get("client_name"),
        job_type=payload.get("job_type"),
        materials_cost=payload["materials_cost"],
        labor_cost=payload["labor_cost"],
        markup_percent=payload["markup_percent"],
        client_action_id=payload["client_action_id"],
    )
    quote_id = result.get("quote_id")
    return {
        **payload,
        "total_amount": result.get("total_amount"),
        "quote_id": quote_id,
        "status": result.get("status", "draft"),
        "_entity": {"type": "quote", "id": quote_id, "client_name": payload.get("client_name", "")},
        "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
    }


@register_handler("construction.quote.list")
async def handle_quote_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    quotes = manager.get_quotes(status=params.get("status"))
    return {
        "count": len(quotes),
        "quotes": quotes[:10],
        "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
    }


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
    manager = get_construction_manager()
    quote_id = params.get("quote_id")
    status = params.get("status", "sent")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            quote_id = resolved["entity"]["id"]

    if not quote_id:
        return {"error": "Which quote?"}

    manager.update_quote_status(int(quote_id), status)
    entity = resolve_quote_by_id(int(quote_id))
    return {
        "client_name": entity.get("client_name", "") if entity else "",
        "status": status,
        "_entity": entity,
        "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
    }


@register_handler("construction.quote.followup")
async def handle_quote_followup(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    quote_id = params.get("quote_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            quote_id = resolved["entity"]["id"]

    if not quote_id:
        return {"error": "Which quote should I follow up on?"}

    result = manager.draft_quote_followup(int(quote_id))
    if result.get("error"):
        return {"error": result["error"]}
    return {
        "message": result.get("message", ""),
        "client_name": result.get("client_name", ""),
        "job_type": result.get("job_type", ""),
        "_ui_action": {"navigate_to": "construction", "tab_index": 1, "highlight_item": int(quote_id)},
    }


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

    manager = get_construction_manager()
    quote_id = int(quote_id)
    payload = manager.prepare_invoice_payload(quote_id)
    if payload.get("error"):
        return {"error": payload["error"]}

    manager.update_quote_status(quote_id, "accepted")
    quote = payload["quote"]
    today = datetime.now()
    due = today + timedelta(days=14)
    inv_num = next_invoice_number()
    invoice_data = {
        **payload["invoice_data"],
        "invoice_number": inv_num,
        "date": today.strftime("%Y-%m-%d"),
        "due_date": due.strftime("%Y-%m-%d"),
    }
    client_data = payload["client_data"]
    pdf_path = generate_invoice_pdf(invoice_data, client_data)
    total = sum(
        float(item.get("qty", 1)) * float(item.get("rate", 0))
        for item in invoice_data["line_items"]
    )

    return {
        "quote_id": quote_id,
        "invoice_number": inv_num,
        "invoice_path": pdf_path,
        "total": total,
        "client_name": quote.get("client_name", ""),
        "_entity": {"type": "quote", "id": quote_id, "client_name": quote.get("client_name", "")},
        "_ui_action": {"navigate_to": "construction", "tab_index": 1, "highlight_item": quote_id, "refresh_data": True},
    }


# ── Payments ─────────────────────────────────────────────────────────────────

@register_handler("construction.payment.record")
async def handle_payment_record(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    quote_id = params.get("quote_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))
    amount = float(params.get("amount", 0))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            quote_id = resolved["entity"]["id"]

    if not quote_id:
        return {"error": "Which quote is this payment for?"}

    result = manager.record_payment(
        quote_id=int(quote_id),
        amount=amount,
        client_action_id=(metadata or {}).get("client_action_id"),
    )
    return {
        "amount": amount,
        "client_name": result.get("client_name", ""),
        "remaining": result.get("remaining", 0),
        "_ui_action": {"navigate_to": "construction", "tab_index": 2, "refresh_data": True},
    }


@register_handler("construction.payment.list")
async def handle_payment_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    payments = manager.get_payments(
        quote_id=int(params["quote_id"]) if params.get("quote_id") else None
    )
    return {
        "count": len(payments),
        "payments": payments[:10],
        "_ui_action": {"navigate_to": "construction", "tab_index": 2, "refresh_data": True},
    }


@register_handler("construction.payment.pipeline")
async def handle_payment_pipeline(params: dict, screen_context: str, metadata: dict | None) -> dict:
    manager = get_construction_manager()
    data = manager.get_pipeline_summary()
    return {
        "total_revenue": data.get("total_revenue", 0),
        "outstanding": data.get("outstanding", data.get("total_pipeline_value", 0)),
        "_ui_action": {"navigate_to": "construction", "tab_index": 2},
    }
