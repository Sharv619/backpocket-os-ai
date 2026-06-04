"""
BackPocket OS — Voice Handlers: Cross-Screen Workflows
Compound intents spanning multiple screens (email→lead, lead→quote, etc).
"""

import logging

from routes._voice_handlers import register_handler
from routes.construction import extract_lead_from_email
from routes.marketing import get_marketing_insights
from services.construction import get_construction_manager
from services.entity_resolver import resolve_entity
from services.invoice_engine import generate_invoice_pdf, next_invoice_number
from services.pending_emails import find_pending_email, get_pending_email_summary
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@register_handler("cross.email_to_lead")
async def handle_email_to_lead(params: dict, screen_context: str, metadata: dict | None) -> dict:
    ref_id = params.get("ref_id", "")
    sender = params.get("sender", "")

    email_data = {}
    item = find_pending_email(ref_id or sender)
    if item:
        email_data = {
            "from": item.get("sender", ""),
            "subject": item.get("subject", ""),
            "body": item.get("body", item.get("preview", "")),
        }

    if not email_data:
        return {"error": "Couldn't find that email. Which one?"}

    data = await extract_lead_from_email(email_data)
    if data.get("status") == "success":
        lead = data.get("extracted_data", {})
        return {
            "lead_id": data.get("lead_id"),
            "client_name": lead.get("client_name", ""),
            "job_type": lead.get("job_type", ""),
            "location": lead.get("location", ""),
            "estimated_budget": lead.get("estimated_budget", 0),
            "urgency": lead.get("urgency", "medium"),
            "_entity": {
                "type": "lead",
                "id": data.get("lead_id"),
                "client_name": lead.get("client_name", ""),
            },
            "_ui_action": {"navigate_to": "construction", "tab_index": 0, "refresh_data": True},
        }
    return {"error": "Failed to extract lead from email."}


@register_handler("cross.lead_to_quote")
async def handle_lead_to_quote(params: dict, screen_context: str, metadata: dict | None) -> dict:
    lead_params = {}
    for key in ("client_name", "job_type", "location", "estimated_budget", "urgency", "email"):
        if key in params:
            lead_params[key] = params[key]

    if lead_params.get("client_name"):
        manager = get_construction_manager()
        result = manager.create_lead(
            client_name=lead_params.get("client_name", ""),
            email=lead_params.get("email", ""),
            job_type=lead_params.get("job_type", ""),
            location=lead_params.get("location", ""),
            urgency=lead_params.get("urgency", "medium"),
            budget=float(lead_params.get("estimated_budget", 0) or 0),
            client_action_id=(metadata or {}).get("client_action_id"),
        )
        lead_id = result.get("lead_id")
        return {
            "lead_created": True,
            "lead_id": lead_id,
            "client_name": lead_params.get("client_name", ""),
            "message": f"Lead saved for {lead_params.get('client_name', '')}. Now for the quote -- materials cost?",
            "_entity": {"type": "lead", "id": lead_id, "client_name": lead_params.get("client_name", "")},
            "_ui_action": {"navigate_to": "construction", "tab_index": 1},
        }

    return {"error": "Need at least a client name to create a lead."}


@register_handler("cross.quote_to_invoice")
async def handle_quote_to_invoice(params: dict, screen_context: str, metadata: dict | None) -> dict:
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
    today = datetime.now()
    due = today + timedelta(days=14)
    invoice_number = next_invoice_number()
    invoice_data = {
        **payload["invoice_data"],
        "invoice_number": invoice_number,
        "date": today.strftime("%Y-%m-%d"),
        "due_date": due.strftime("%Y-%m-%d"),
    }
    invoice_path = generate_invoice_pdf(invoice_data, payload["client_data"])
    total = sum(
        float(item.get("qty", 1)) * float(item.get("rate", 0))
        for item in invoice_data["line_items"]
    )
    return {
        "quote_id": quote_id,
        "status": "accepted",
        "invoice_number": invoice_number,
        "invoice_path": invoice_path,
        "total": total,
        "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
    }

    return {"error": "Failed to generate invoice."}


@register_handler("cross.quote_to_followup")
async def handle_quote_to_followup(params: dict, screen_context: str, metadata: dict | None) -> dict:
    quote_id = params.get("quote_id")
    fuzzy = params.get("fuzzy", params.get("fuzzy_ref", ""))

    if not quote_id and fuzzy:
        resolved = resolve_entity("quote", str(fuzzy))
        if resolved["match"] in ("exact", "fuzzy") and resolved["entity"]:
            quote_id = resolved["entity"]["id"]

    if not quote_id:
        return {"error": "Which quote should I follow up on?"}

    manager = get_construction_manager()
    result = manager.draft_quote_followup(int(quote_id))
    if result.get("error"):
        return {"error": result["error"]}
    return {
        "quote_id": quote_id,
        "follow_up_message": result.get("message", ""),
        "client_name": result.get("client_name", ""),
        "job_type": result.get("job_type", ""),
        "_ui_action": {"navigate_to": "construction", "tab_index": 1, "highlight_item": quote_id},
    }

    return {"error": "Couldn't generate follow-up. Check the quote ID."}


@register_handler("cross.full_report")
async def handle_full_report(params: dict, screen_context: str, metadata: dict | None) -> dict:
    report = {}
    pending = get_pending_email_summary()
    pipeline = get_construction_manager().get_pipeline_summary()

    report["emails"] = pending.get("pending_count", 0)
    report["urgent"] = pending.get("urgent_count", 0)
    report["pipeline_total"] = pipeline.get("total_pipeline_value", 0)
    report["total_quotes"] = pipeline.get("total_quotes", 0)
    report["accepted"] = pipeline.get("accepted_count", 0)
    report["pending"] = pipeline.get("pending_count", 0)

    try:
        report["marketing"] = await get_marketing_insights()
    except Exception:
        pass

    parts = []
    if report.get("emails"):
        parts.append(f"Inbox: {report['emails']} emails, {report.get('urgent', 0)} urgent")
    if report.get("pipeline_total"):
        parts.append(f"Pipeline: ${report['pipeline_total']:,.0f} across {report.get('total_quotes', 0)} quotes, {report.get('accepted', 0)} accepted, {report.get('pending', 0)} pending")

    report["summary"] = ". ".join(parts) + "." if parts else "No data available."
    report["_ui_action"] = {"navigate_to": "dashboard"}
    return report
