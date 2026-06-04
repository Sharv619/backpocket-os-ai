"""
BackPocket OS — Voice Handlers: Dashboard
Handles dashboard.summary, pending_count, pipeline_summary, navigate, growth_stats.
"""

import logging

from routes._voice_handlers import register_handler
from routes.marketing import get_marketing_insights
from services.construction import get_construction_manager
from services.pending_emails import get_pending_email_summary

logger = logging.getLogger(__name__)


@register_handler("dashboard.summary")
async def handle_dashboard_summary(params: dict, screen_context: str, metadata: dict | None) -> dict:
    pending = get_pending_email_summary()
    pipeline = get_construction_manager().get_pipeline_summary()
    result = {
        "pending_count": pending.get("pending_count", 0),
        "urgent_count": pending.get("urgent_count", 0),
        "pipeline_total": pipeline.get("total_pipeline_value", 0),
        "total_quotes": pipeline.get("total_quotes", 0),
        "accepted_quotes": pipeline.get("accepted_count", 0),
    }

    result["_ui_action"] = {"navigate_to": "dashboard", "refresh_data": True}
    return result


@register_handler("dashboard.pending_count")
async def handle_pending_count(params: dict, screen_context: str, metadata: dict | None) -> dict:
    pending = get_pending_email_summary()
    return {
        "pending_count": pending.get("pending_count", 0),
        "urgent_count": pending.get("urgent_count", 0),
    }


@register_handler("dashboard.pipeline_summary")
async def handle_pipeline_summary(params: dict, screen_context: str, metadata: dict | None) -> dict:
    data = get_construction_manager().get_pipeline_summary()
    return {
        "pipeline_total": data.get("total_pipeline_value", 0),
        "pending_quotes": data.get("pending_count", 0),
        "accepted_quotes": data.get("accepted_count", 0),
        "total_quotes": data.get("total_quotes", 0),
    }


@register_handler("dashboard.growth_stats")
async def handle_growth_stats(params: dict, screen_context: str, metadata: dict | None) -> dict:
    try:
        data = await get_marketing_insights()
        insights = data.get("insights", {})
        return {
            "search_growth": insights.get("local_search_impressions", {}).get("value", ""),
            "insights": data,
        }
    except Exception as e:
        logger.warning(f"Marketing insights fetch failed: {e}")
    return {"search_growth": "unavailable"}
