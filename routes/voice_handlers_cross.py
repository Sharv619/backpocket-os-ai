"""
BackPocket OS — Voice Handlers: Cross-Screen Workflows
Compound intents spanning multiple screens (email→lead, lead→quote, etc).
"""

import logging
import httpx

from routes._voice_handlers import register_handler
from services.entity_resolver import resolve_entity

logger = logging.getLogger(__name__)

BASE = "http://127.0.0.1:8000"


@register_handler("cross.email_to_lead")
async def handle_email_to_lead(params: dict, screen_context: str, metadata: dict | None) -> dict:
    ref_id = params.get("ref_id", "")
    sender = params.get("sender", "")

    email_data = {}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE}/api/mobile/pending")
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            search = (ref_id or sender).lower()
            for item in items:
                if search in (item.get("sender", "") + item.get("subject", "")).lower():
                    email_data = {
                        "from": item.get("sender", ""),
                        "subject": item.get("subject", ""),
                        "body": item.get("body", item.get("preview", "")),
                    }
                    break

    if not email_data:
        return {"error": "Couldn't find that email. Which one?"}

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
                "urgency": lead.get("urgency", "medium"),
                "_entity": {"type": "lead", "id": lead.get("lead_id"), "client_name": lead.get("client_name", "")},
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
        lead_payload = {
            "client_name": lead_params.get("client_name", ""),
            "email": lead_params.get("email", ""),
            "job_type": lead_params.get("job_type", ""),
            "location": lead_params.get("location", ""),
            "urgency": lead_params.get("urgency", "medium"),
            "estimated_budget": int(float(lead_params.get("estimated_budget", 0))),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{BASE}/api/construction/leads", json=lead_payload)
            if resp.status_code == 200:
                data = resp.json()
                lead_id = data.get("lead_id", data.get("id"))
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

    async with httpx.AsyncClient(timeout=15) as client:
        await client.patch(f"{BASE}/api/construction/quotes/{quote_id}", json={"status": "accepted"})

        resp = await client.post(f"{BASE}/api/invoice/generate", json={"quote_id": int(quote_id)})
        if resp.status_code == 200:
            data = resp.json()
            return {
                "quote_id": quote_id,
                "status": "accepted",
                "invoice_url": data.get("url", ""),
                "total": data.get("total", 0),
                "_ui_action": {"navigate_to": "construction", "tab_index": 1, "refresh_data": True},
            }

    return {"error": "Failed to generate invoice."}


@register_handler("cross.full_report")
async def handle_full_report(params: dict, screen_context: str, metadata: dict | None) -> dict:
    report = {}
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{BASE}/api/status")
            if resp.status_code == 200:
                status = resp.json()
                report["emails"] = status.get("pending_emails", 0)
                report["urgent"] = status.get("urgent_count", 0)
        except Exception:
            pass

        try:
            resp = await client.get(f"{BASE}/api/construction/pipeline")
            if resp.status_code == 200:
                data = resp.json().get("data", resp.json())
                report["pipeline_total"] = data.get("total_pipeline_value", 0)
                report["total_quotes"] = data.get("total_quotes", 0)
                report["accepted"] = data.get("accepted_count", 0)
                report["pending"] = data.get("pending_count", 0)
        except Exception:
            pass

        try:
            resp = await client.get(f"{BASE}/api/marketing/insights")
            if resp.status_code == 200:
                report["marketing"] = resp.json()
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
