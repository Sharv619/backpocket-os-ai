"""
BackPocket OS — Voice Response Generator
Generates natural-language TTS responses from structured action results.
Tradie tone: casual, direct, Australian.
"""

import logging

logger = logging.getLogger(__name__)


def generate_response(intent: str, result: dict, action: str = "execute") -> str:
    """Generate a natural speech response for a completed voice action."""
    generator = RESPONSE_GENERATORS.get(intent)
    if generator:
        try:
            return generator(result, action)
        except Exception as e:
            logger.error(f"Response generation error for {intent}: {e}")
    return _generic_response(intent, result, action)


def generate_confirmation_prompt(intent: str, params: dict, strong: bool = False) -> str:
    """Generate a confirmation prompt before executing an action."""
    generator = CONFIRM_GENERATORS.get(intent)
    if generator:
        try:
            return generator(params, strong)
        except Exception as e:
            logger.error(f"Confirmation generation error for {intent}: {e}")
    return _generic_confirm(intent, params, strong)


def generate_error_response(error_type: str, details: str = "") -> str:
    messages = {
        "transcription_failed": "Sorry, didn't catch that. Try again?",
        "low_confidence": "Not sure what you mean. Can you say that differently?",
        "server_error": f"That didn't work{f' -- {details}' if details else ''}. Want to try again?",
        "session_expired": "We were working on something but it timed out. Want to start over?",
        "no_connection": "Can't reach the server. Check your connection in Settings.",
        "no_results": f"Couldn't find anything{f' for {details}' if details else ''}.",
        "permission_denied": "Need mic access to use voice. Check your permissions.",
    }
    return messages.get(error_type, "Something went wrong. Try again?")


def generate_disambiguation(entity_type: str, candidates: list) -> str:
    """Generate a response when multiple entities match a fuzzy reference."""
    names = []
    for c in candidates[:5]:
        name = c.get("client_name") or c.get("sender") or c.get("name", "unknown")
        location = c.get("location", "")
        if location:
            names.append(f"{name} ({location})")
        else:
            names.append(name)

    joined = ", ".join(names[:-1]) + f", or {names[-1]}" if len(names) > 2 else " or ".join(names)
    return f"Found {len(candidates)} {entity_type}s -- {joined}?"


def generate_collecting_response(intent: str, question: str, collected: dict) -> str:
    """Generate a response during multi-turn param collection."""
    if not collected:
        return question

    summary_parts = []
    for key, val in collected.items():
        key.replace("_", " ")
        summary_parts.append(f"{val}")

    return f"Got it. {question}"


# ── Dashboard responses ──────────────────────────────────────────────────────

def _dashboard_summary(result: dict, action: str) -> str:
    emails = result.get("pending_count", 0)
    urgent = result.get("urgent_count", 0)
    pipeline = result.get("pipeline_total", 0)
    quotes = result.get("total_quotes", 0)
    accepted = result.get("accepted_quotes", 0)

    parts = []
    if emails:
        parts.append(f"You've got {emails} emails waiting" + (f", {urgent} urgent" if urgent else ""))
    if pipeline:
        parts.append(f"Pipeline's sitting at ${pipeline:,.0f} across {quotes} quotes, {accepted} accepted")
    return ". ".join(parts) + "." if parts else "All quiet today."


def _dashboard_pending(result: dict, action: str) -> str:
    count = result.get("pending_count", 0)
    urgent = result.get("urgent_count", 0)
    if count == 0:
        return "Inbox is clear, no emails waiting."
    msg = f"You've got {count} emails waiting"
    if urgent:
        msg += f", {urgent} are urgent"
    return msg + "."


def _dashboard_pipeline(result: dict, action: str) -> str:
    total = result.get("pipeline_total", 0)
    pending = result.get("pending_quotes", 0)
    accepted = result.get("accepted_quotes", 0)
    return f"Pipeline's at ${total:,.0f}. {pending} pending quotes, {accepted} accepted."


# ── Inbox responses ──────────────────────────────────────────────────────────

def _inbox_approve(result: dict, action: str) -> str:
    recipient = result.get("recipient", "them")
    return f"Done, email's sent to {recipient}."


def _inbox_approve_batch(result: dict, action: str) -> str:
    count = result.get("count", 0)
    return f"All {count} sent. Inbox updated."


def _inbox_list(result: dict, action: str) -> str:
    count = result.get("count", 0)
    if count == 0:
        return "Inbox is empty."
    return f"You've got {count} emails in the inbox."


# ── Construction: Leads ──────────────────────────────────────────────────────

def _lead_create(result: dict, action: str) -> str:
    name = result.get("client_name", "")
    job = result.get("job_type", "")
    location = result.get("location", "")
    budget = result.get("estimated_budget", 0)
    parts = [name, job, location]
    if budget:
        parts.append(f"${budget:,.0f}")
    return f"Lead saved. {', '.join(p for p in parts if p)}."


def _lead_list(result: dict, action: str) -> str:
    count = result.get("count", 0)
    if count == 0:
        return "No leads yet."
    return f"You've got {count} leads."


def _lead_detail(result: dict, action: str) -> str:
    name = result.get("client_name", "Unknown")
    job = result.get("job_type", "")
    location = result.get("location", "")
    status = result.get("status", "")
    budget = result.get("estimated_budget", 0)
    msg = f"{name} -- {job} in {location}"
    if budget:
        msg += f", budget ${budget:,.0f}"
    if status:
        msg += f". Status: {status}"
    return msg + "."


def _lead_update(result: dict, action: str) -> str:
    name = result.get("client_name", "lead")
    status = result.get("status", "updated")
    return f"{name} marked as {status}."


# ── Construction: Quotes ─────────────────────────────────────────────────────

def _quote_create(result: dict, action: str) -> str:
    total = result.get("total_amount", 0)
    materials = result.get("materials_cost", 0)
    labor = result.get("labor_cost", 0)
    markup = result.get("markup_percent", 20)
    return f"Quote saved. ${total:,.0f} total -- materials ${materials:,.0f} + labor ${labor:,.0f} + {markup}% markup."


def _quote_list(result: dict, action: str) -> str:
    count = result.get("count", 0)
    if count == 0:
        return "No quotes yet."
    return f"You've got {count} quotes."


def _quote_detail(result: dict, action: str) -> str:
    name = result.get("client_name", "")
    total = result.get("total_amount", 0)
    status = result.get("status", "")
    return f"{name} -- ${total:,.0f}, status: {status}."


def _quote_update(result: dict, action: str) -> str:
    name = result.get("client_name", "quote")
    status = result.get("status", "updated")
    return f"{name}'s quote marked as {status}."


def _quote_followup(result: dict, action: str) -> str:
    message = result.get("message", "")
    return f"Here's the follow-up: {message}" if message else "Follow-up drafted."


# ── Construction: Payments ───────────────────────────────────────────────────

def _payment_record(result: dict, action: str) -> str:
    amount = result.get("amount", 0)
    name = result.get("client_name", "")
    remaining = result.get("remaining", 0)
    msg = f"Payment of ${amount:,.0f} recorded"
    if name:
        msg += f" from {name}"
    if remaining:
        msg += f". ${remaining:,.0f} still outstanding"
    return msg + "."


def _payment_list(result: dict, action: str) -> str:
    count = result.get("count", 0)
    return f"{count} payments on record." if count else "No payments recorded yet."


def _payment_pipeline(result: dict, action: str) -> str:
    total = result.get("total_revenue", 0)
    outstanding = result.get("outstanding", 0)
    return f"Total revenue ${total:,.0f}, outstanding ${outstanding:,.0f}."


# ── Documents ────────────────────────────────────────────────────────────────

def _documents_list(result: dict, action: str) -> str:
    count = result.get("count", 0)
    analyzed = result.get("analyzed", 0)
    return f"You've got {count} documents. {analyzed} analyzed." if count else "No documents yet."


def _documents_analyze(result: dict, action: str) -> str:
    summary = result.get("summary", "Analysis complete.")
    return summary


# ── Marketing ────────────────────────────────────────────────────────────────

def _marketing_post(result: dict, action: str) -> str:
    return "Posted. Should show up on your Google Business Profile within the hour."


def _marketing_insights(result: dict, action: str) -> str:
    growth = result.get("search_growth", "")
    return f"Local search is {growth}." if growth else "Marketing insights loaded."


# ── Instructions ─────────────────────────────────────────────────────────────

def _instructions_add(result: dict, action: str) -> str:
    return "Saved. Pip will follow this from now on."


def _instructions_list(result: dict, action: str) -> str:
    count = result.get("count", 0)
    return f"You've got {count} active instructions." if count else "No instructions set yet."


def _instructions_delete(result: dict, action: str) -> str:
    return "Instruction removed."


# ── Navigation ───────────────────────────────────────────────────────────────

def _navigate(result: dict, action: str) -> str:
    return ""


# ── Meta ─────────────────────────────────────────────────────────────────────

def _meta_help(result: dict, action: str) -> str:
    return "You can say things like 'show me my leads', 'create a quote', 'what's my pipeline', or 'go to inbox'. Say 'help' on any screen for specific commands."


def _meta_cancel(result: dict, action: str) -> str:
    return "Cancelled."


def _meta_undo(result: dict, action: str) -> str:
    undone = result.get("description", "last action")
    return f"Reverted: {undone}."


# ── Cross-screen ─────────────────────────────────────────────────────────────

def _cross_full_report(result: dict, action: str) -> str:
    return result.get("summary", "Report generated.")


# ── Generic fallbacks ────────────────────────────────────────────────────────

def _generic_response(intent: str, result: dict, action: str) -> str:
    if action == "navigate":
        return ""
    if action == "display":
        return "Here you go."
    return "Done."


def _generic_confirm(intent: str, params: dict, strong: bool) -> str:
    action_word = intent.split(".")[-1] if intent else "do this"
    suffix = " Say 'do it' to confirm." if not strong else " Say 'confirmed' to proceed."
    details = ", ".join(f"{k}: {v}" for k, v in params.items() if v is not None)
    return f"About to {action_word} -- {details}.{suffix}" if details else f"About to {action_word}.{suffix}"


# ── Confirmation prompt generators ───────────────────────────────────────────

def _confirm_lead_create(params: dict, strong: bool) -> str:
    name = params.get("client_name", "")
    job = params.get("job_type", "")
    location = params.get("location", "")
    budget = params.get("estimated_budget", "")
    parts = [name, job, location]
    if budget:
        parts.append(f"${int(budget):,}")
    detail = ", ".join(p for p in parts if p)
    return f"Lead: {detail}. Save it?"


def _confirm_quote_create(params: dict, strong: bool) -> str:
    materials = params.get("materials_cost", 0)
    labor = params.get("labor_cost", 0)
    markup = params.get("markup_percent", 20)
    total = (float(materials) + float(labor)) * (1 + float(markup) / 100)
    return f"Quote total: ${total:,.0f}. Materials ${float(materials):,.0f} + labor ${float(labor):,.0f} + {markup}% markup. Save it?"


def _confirm_payment_record(params: dict, strong: bool) -> str:
    amount = params.get("amount", 0)
    return f"Recording ${float(amount):,.0f} payment. Say 'confirmed' to proceed."


def _confirm_approve(params: dict, strong: bool) -> str:
    recipient = params.get("recipient", params.get("sender", "them"))
    return f"Send the email to {recipient}? Say 'send it' to confirm."


def _confirm_approve_batch(params: dict, strong: bool) -> str:
    count = params.get("count", 0)
    items = params.get("items", [])
    if items:
        names = ", ".join(items[:4])
        return f"That's {count} emails to: {names}. Say 'send them all' to confirm."
    return f"Approve all {count} emails? Say 'send them all' to confirm."


RESPONSE_GENERATORS = {
    "dashboard.summary": _dashboard_summary,
    "dashboard.pending_count": _dashboard_pending,
    "dashboard.pipeline_summary": _dashboard_pipeline,
    "dashboard.navigate": _navigate,
    "dashboard.growth_stats": _marketing_insights,
    "inbox.list": _inbox_list,
    "inbox.approve": _inbox_approve,
    "inbox.approve_batch": _inbox_approve_batch,
    "construction.lead.create": _lead_create,
    "construction.lead.list": _lead_list,
    "construction.lead.detail": _lead_detail,
    "construction.lead.update": _lead_update,
    "construction.lead.extract": _lead_create,
    "construction.quote.create": _quote_create,
    "construction.quote.list": _quote_list,
    "construction.quote.detail": _quote_detail,
    "construction.quote.update": _quote_update,
    "construction.quote.followup": _quote_followup,
    "construction.payment.record": _payment_record,
    "construction.payment.list": _payment_list,
    "construction.payment.pipeline": _payment_pipeline,
    "documents.list": _documents_list,
    "documents.analyze": _documents_analyze,
    "marketing.create_post": _marketing_post,
    "marketing.insights": _marketing_insights,
    "instructions.list": _instructions_list,
    "instructions.add": _instructions_add,
    "instructions.delete": _instructions_delete,
    "navigate.screen": _navigate,
    "meta.help": _meta_help,
    "meta.cancel": _meta_cancel,
    "meta.undo": _meta_undo,
    "cross.full_report": _cross_full_report,
}

CONFIRM_GENERATORS = {
    "construction.lead.create": _confirm_lead_create,
    "construction.quote.create": _confirm_quote_create,
    "construction.payment.record": _confirm_payment_record,
    "inbox.approve": _confirm_approve,
    "inbox.approve_batch": _confirm_approve_batch,
}
