"""
BackPocket OS — Voice Handlers: Dashboard
Handles dashboard.summary, pending_count, pipeline_summary, navigate, growth_stats.
"""

import logging
import httpx

from routes._voice_handlers import register_handler

logger = logging.getLogger(__name__)

BASE = "http://127.0.0.1:8000"


@register_handler("dashboard.summary")
async def handle_dashboard_summary(params: dict, screen_context: str, metadata: dict | None) -> dict:
    result = {}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            status_resp = await client.get(f"{BASE}/api/status")
            if status_resp.status_code == 200:
                status = status_resp.json()
                result["pending_count"] = status.get("pending_emails", 0)
                result["urgent_count"] = status.get("urgent_count", 0)
        except Exception as e:
            logger.warning(f"Status fetch failed: {e}")

        try:
            pipeline_resp = await client.get(f"{BASE}/api/construction/pipeline")
            if pipeline_resp.status_code == 200:
                data = pipeline_resp.json().get("data", pipeline_resp.json())
                result["pipeline_total"] = data.get("total_pipeline_value", 0)
                result["total_quotes"] = data.get("total_quotes", 0)
                result["accepted_quotes"] = data.get("accepted_count", 0)
        except Exception as e:
            logger.warning(f"Pipeline fetch failed: {e}")

    result["_ui_action"] = {"navigate_to": "dashboard", "refresh_data": True}
    return result


@register_handler("dashboard.pending_count")
async def handle_pending_count(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/mobile/pending")
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                urgent = sum(1 for i in items if i.get("tier", 5) <= 1)
                return {"pending_count": len(items), "urgent_count": urgent}
        except Exception as e:
            logger.warning(f"Pending fetch failed: {e}")
    return {"pending_count": 0, "urgent_count": 0}


@register_handler("dashboard.pipeline_summary")
async def handle_pipeline_summary(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/construction/pipeline")
            if resp.status_code == 200:
                data = resp.json().get("data", resp.json())
                return {
                    "pipeline_total": data.get("total_pipeline_value", 0),
                    "pending_quotes": data.get("pending_count", 0),
                    "accepted_quotes": data.get("accepted_count", 0),
                    "total_quotes": data.get("total_quotes", 0),
                }
        except Exception as e:
            logger.warning(f"Pipeline fetch failed: {e}")
    return {"pipeline_total": 0, "pending_quotes": 0, "accepted_quotes": 0}


@register_handler("dashboard.growth_stats")
async def handle_growth_stats(params: dict, screen_context: str, metadata: dict | None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{BASE}/api/marketing/insights")
            if resp.status_code == 200:
                data = resp.json()
                return {"search_growth": data.get("growth", ""), "insights": data}
        except Exception as e:
            logger.warning(f"Marketing insights fetch failed: {e}")
    return {"search_growth": "unavailable"}
