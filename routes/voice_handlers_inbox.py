"""
BackPocket OS — Voice Handlers: Inbox
Handles inbox.list, filter_tier, approve, approve_batch, show_draft, revise_draft, read_email, count_by_tier.
"""

import logging
import httpx

from routes._voice_handlers import register_handler

logger = logging.getLogger(__name__)

BASE = "http://127.0.0.1:8000"


async def _fetch_pending() -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE}/api/mobile/pending")
        if resp.status_code == 200:
            return resp.json().get("items", [])
    return []


def _match_email(items: list, ref: str) -> dict | None:
    ref_lower = ref.lower()
    for item in items:
        sender = (item.get("sender") or "").lower()
        subject = (item.get("subject") or "").lower()
        if ref_lower in sender or ref_lower in subject:
            return item
    return None


@register_handler("inbox.list")
async def handle_inbox_list(params: dict, screen_context: str, metadata: dict | None) -> dict:
    items = await _fetch_pending()
    return {
        "count": len(items),
        "_ui_action": {"navigate_to": "inbox", "refresh_data": True},
    }


@register_handler("inbox.filter_tier")
async def handle_inbox_filter(params: dict, screen_context: str, metadata: dict | None) -> dict:
    tier = params.get("tier", 1)
    try:
        tier = int(tier)
    except (ValueError, TypeError):
        tier_map = {"urgent": 1, "high": 2, "medium": 3, "low": 4, "spam": 5}
        tier = tier_map.get(str(tier).lower(), 1)

    items = await _fetch_pending()
    filtered = [i for i in items if i.get("tier", 5) <= tier]
    return {
        "count": len(filtered),
        "tier": tier,
        "_ui_action": {"navigate_to": "inbox", "filter_tier": tier},
    }


@register_handler("inbox.approve")
async def handle_inbox_approve(params: dict, screen_context: str, metadata: dict | None) -> dict:
    ref_id = params.get("ref_id")
    sender = params.get("sender", "")
    subject = params.get("subject", "")

    if not ref_id and (sender or subject):
        items = await _fetch_pending()
        match = _match_email(items, sender or subject)
        if match:
            ref_id = match.get("ref_id")

    if not ref_id:
        return {"error": "Couldn't find the email. Which one?"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{BASE}/api/mobile/approve",
            json={"ref_id": ref_id, "note": "approved via voice"},
        )
        if resp.status_code == 200:
            return {
                "recipient": sender or ref_id,
                "_ui_action": {"navigate_to": "inbox", "refresh_data": True},
            }

    return {"error": "Failed to approve email."}


@register_handler("inbox.approve_batch")
async def handle_inbox_approve_batch(params: dict, screen_context: str, metadata: dict | None) -> dict:
    tier = params.get("tier", 1)
    try:
        tier = int(tier)
    except (ValueError, TypeError):
        tier = 1

    items = await _fetch_pending()
    to_approve = [i for i in items if i.get("tier", 5) <= tier]

    approved = 0
    async with httpx.AsyncClient(timeout=30) as client:
        for item in to_approve:
            try:
                resp = await client.post(
                    f"{BASE}/api/mobile/approve",
                    json={"ref_id": item["ref_id"], "note": "batch approved via voice"},
                )
                if resp.status_code == 200:
                    approved += 1
            except Exception as e:
                logger.warning(f"Batch approve failed for {item.get('ref_id')}: {e}")

    return {
        "count": approved,
        "items": [i.get("sender", "") for i in to_approve],
        "_ui_action": {"navigate_to": "inbox", "refresh_data": True},
    }


@register_handler("inbox.show_draft")
async def handle_show_draft(params: dict, screen_context: str, metadata: dict | None) -> dict:
    sender = params.get("sender", params.get("ref_id", ""))
    items = await _fetch_pending()
    match = _match_email(items, sender)
    if match:
        return {
            "sender": match.get("sender", ""),
            "subject": match.get("subject", ""),
            "draft": match.get("draft_body", match.get("body", "")),
            "_ui_action": {"navigate_to": "inbox", "highlight_item": match.get("ref_id")},
        }
    return {"error": f"Couldn't find an email from {sender}."}


@register_handler("inbox.revise_draft")
async def handle_revise_draft(params: dict, screen_context: str, metadata: dict | None) -> dict:
    ref_id = params.get("ref_id", "")
    instructions = params.get("instructions", "")

    if not ref_id:
        return {"error": "Which draft should I revise?"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{BASE}/api/revise",
            json={"ref_id": ref_id, "instructions": instructions},
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "revised_draft": data.get("revised", ""),
                "_ui_action": {"navigate_to": "inbox", "highlight_item": ref_id, "refresh_data": True},
            }
    return {"error": "Failed to revise draft."}


@register_handler("inbox.read_email")
async def handle_read_email(params: dict, screen_context: str, metadata: dict | None) -> dict:
    sender_name = params.get("sender_name", params.get("sender", ""))
    items = await _fetch_pending()
    match = _match_email(items, sender_name)
    if match:
        return {
            "sender": match.get("sender", ""),
            "subject": match.get("subject", ""),
            "body": match.get("body", match.get("preview", "")),
            "draft": match.get("draft_body", ""),
        }
    return {"error": f"Couldn't find an email from {sender_name}."}


@register_handler("inbox.count_by_tier")
async def handle_count_by_tier(params: dict, screen_context: str, metadata: dict | None) -> dict:
    items = await _fetch_pending()
    counts = {}
    for item in items:
        t = item.get("tier", 5)
        counts[t] = counts.get(t, 0) + 1

    tier_labels = {1: "urgent", 2: "high", 3: "medium", 4: "low", 5: "spam"}
    summary = ", ".join(f"{counts.get(t, 0)} {tier_labels[t]}" for t in sorted(counts.keys()))
    return {"counts": counts, "summary": summary}
