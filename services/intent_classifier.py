"""
BackPocket OS — Voice Intent Classifier
Gemini-powered intent classification + entity extraction for voice commands.
"""

import json
import logging
from services.gemini import get_gemini_client

logger = logging.getLogger(__name__)

INTENT_TAXONOMY = """
INTENT TAXONOMY (dot-notation: screen.entity.action):

# Dashboard
dashboard.summary          — "What's going on today?", "Give me the rundown"
dashboard.pending_count    — "How many emails?", "How many pending?"
dashboard.pipeline_summary — "What's my pipeline?", "How are the jobs?"
dashboard.navigate         — "Go to inbox", "Open construction"
dashboard.growth_stats     — "How's my SEO?", "Marketing numbers?"

# Inbox
inbox.list                 — "Show me emails", "What's in my inbox?"
inbox.filter_tier          — "Show urgent ones", "Just tier 1"
inbox.approve              — "Approve that one", "Fire off the email to [name]"
inbox.approve_batch        — "Approve all tier 1", "Send all urgent"
inbox.show_draft           — "Show me the draft to [name]"
inbox.revise_draft         — "Make it more casual", "Rewrite that"
inbox.read_email           — "Read me [name]'s email"
inbox.count_by_tier        — "How many urgent emails?"

# Chat (fallback)
chat.ask                   — Any free-form question
chat.clear                 — "Start fresh", "New chat"

# Documents
documents.list             — "Show me my documents"
documents.upload           — "Scan a document", "Take a photo"
documents.analyze          — "Analyze that document", "What does this say?"
documents.search           — "Find the invoice from March"

# Marketing
marketing.create_post      — "Create a Google post about [job] in [suburb]"
marketing.insights         — "How's my local SEO?"
marketing.activity         — "Show me recent posts"

# Instructions
instructions.list          — "What rules do I have?"
instructions.add           — "New rule: [text]"
instructions.delete        — "Delete the [keyword] instruction"

# Construction: Leads
construction.lead.create   — "Create a lead for [name], [job] in [suburb], budget [amount]"
construction.lead.list     — "Show me all leads"
construction.lead.detail   — "Tell me about the [suburb] lead"
construction.lead.update   — "Mark the [suburb] lead as contacted"
construction.lead.extract  — "Extract a lead from that email"

# Construction: Quotes
construction.quote.create  — "Generate a quote for the [suburb] job"
construction.quote.list    — "Show me all quotes"
construction.quote.detail  — "What's the total on the [suburb] quote?"
construction.quote.update  — "They accepted the [suburb] quote"
construction.quote.followup — "Draft a follow-up for the [suburb] quote"
construction.quote.invoice — "Bang out an invoice for quote [id]"

# Construction: Payments
construction.payment.record  — "Record $[amount] payment from [name]"
construction.payment.list    — "Show me payments", "Who's paid?"
construction.payment.pipeline — "What's the damage?", "How much outstanding?"

# Cross-screen
cross.email_to_lead        — "That email looks like a lead, extract it"
cross.lead_to_quote        — "Create a lead and generate a quote"
cross.quote_to_invoice     — "The [suburb] job is done, invoice them"
cross.quote_to_followup    — "Follow up with the [suburb] bloke about his quote", "Chase up the Campbelltown quote"
cross.full_report          — "Give me the full rundown on the business"

# Navigation
navigate.screen            — "Go to [screen]", "Take me to [screen]"

# Meta
meta.help                  — "What can I say?", "Help"
meta.cancel                — "Cancel", "Never mind"
meta.undo                  — "Undo that"
"""

TRADIE_SLANG = """
TRADIE SLANG GUIDE:
- "chuck a quote together" = create quote
- "give it the tick" = approve
- "knock it back" = reject
- "what's the damage" = get total / pipeline summary
- "bang out an invoice" = generate invoice
- "fire off that email" = approve and send
- "suss out" = analyze / review
- "that bloke in [suburb]" = fuzzy match by location
- "arvo" = afternoon
- "reckon" = estimate
- "she'll be right" = approve / confirm
"""

SCREEN_NAMES = {
    "dashboard", "inbox", "chat", "documents",
    "marketing", "instructions", "construction", "settings",
}

# Built once at import — avoids re-joining large static strings on every call
_BASE_PROMPT = (
    "You are the voice command classifier for BackPocket OS, a tradie business app.\n"
    "The user is Steve, an Australian contractor. He speaks casually.\n\n"
    + INTENT_TAXONOMY
    + "\n"
    + TRADIE_SLANG
    + "\nClassify the following voice command. Extract all parameters you can from the text.\n"
    "For fuzzy references like \"the Penrith one\" or \"that bloke\", extract the keyword as a fuzzy_ref.\n\n"
    "Return JSON with exactly these fields:\n"
    '{\n  "intent": "screen.entity.action",\n  "entities": {},\n'
    '  "confidence": 0.0-1.0,\n  "ambiguity_reason": null or "reason string"\n}'
)


async def classify_intent(
    transcript: str,
    screen_context: str,
    session_state: dict | None = None,
    available_entities: dict | None = None,
) -> dict:
    """Classify a voice transcript into an intent with extracted entities."""
    client = get_gemini_client()
    if not client:
        return _fallback(transcript)

    session_info = ""
    if session_state and session_state.get("state") == "COLLECTING":
        session_info = (
            f"\nACTIVE SESSION: Collecting params for intent '{session_state['intent']}'. "
            f"Already collected: {session_state.get('collected_params', {})}. "
            f"Still need: {session_state.get('missing_params', [])}. "
            f"The user is likely answering: '{session_state.get('next_question', '')}'"
        )

    entity_context = ""
    if available_entities:
        entity_context = f"\nAVAILABLE DATA CONTEXT:\n{json.dumps(available_entities, default=str)[:2000]}"

    prompt = (
        f"Current screen: {screen_context}\n"
        f"{session_info}\n"
        f"{entity_context}\n\n"
        + _BASE_PROMPT
        + f'\n\nCommand: "{transcript}"'
    )

    try:
        from google.genai import types as genai_types
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip() if response and response.text else ""
        if text:
            result = json.loads(text)
            if "intent" in result and "confidence" in result:
                result.setdefault("entities", {})
                result.setdefault("ambiguity_reason", None)
                return result
    except Exception as e:
        logger.error(f"Intent classification error: {e}")

    return _fallback(transcript)


def _fallback(transcript: str) -> dict:
    """Fallback when Gemini unavailable — route everything to chat."""
    return {
        "intent": "chat.ask",
        "entities": {"message": transcript},
        "confidence": 0.3,
        "ambiguity_reason": "AI classifier unavailable, falling back to chat",
    }
