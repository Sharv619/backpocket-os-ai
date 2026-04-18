import logging
from datetime import datetime
from fastapi import APIRouter
from app.models.schemas import GBPPostRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/marketing/gbp-post")
async def create_gbp_post(request: GBPPostRequest):
    try:
        from services.gemini import get_openrouter_response, get_gemini_client

        prompt = (
            f"Write a 2-sentence Google Business Profile post for a tradie business "
            f"in {request.suburb}, Australia. "
            f"The job was: {request.job_description}. "
            f"Tone: friendly, local, professional. Mention the suburb. "
            f"End with a call-to-action like 'Call us for a free quote!' "
            f"Return ONLY the post text, no quotes or labels."
        )

        post_text = None

        post_text = get_openrouter_response(
            prompt,
            model="google/gemma-3-27b-it:free",
            sys_prompt="You are a local tradie marketing assistant. Write punchy, local GBP posts.",
        )

        if not post_text:
            client = get_gemini_client()
            if client:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                post_text = (
                    response.text.strip() if response and response.text else None
                )

        if not post_text:
            post_text = (
                f"Just completed a job in {request.suburb}! "
                f"{request.job_description} - done right, on time. "
                f"Call us for a free quote!"
            )

        conn = __import__("sqlite3").connect("backpocket.db")
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO marketing_activity
               (activity_type, job_description, suburb, generated_post, status)
               VALUES (?, ?, ?, ?, ?)""",
            ("gbp_post", request.job_description, request.suburb, post_text, "draft"),
        )
        activity_id = cur.lastrowid
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "activity_id": activity_id,
            "post": post_text,
            "suburb": request.suburb,
            "note": "Post drafted and saved. Mark as 'posted' when live on GBP.",
        }
    except Exception as e:
        logger.error(f"GBP post error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/api/marketing/activity")
async def get_marketing_activity(limit: int = 20):
    try:
        conn = __import__("sqlite3").connect("backpocket.db")
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM marketing_activity ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"count": len(rows), "activity": rows}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/api/marketing/insights")
async def get_marketing_insights():
    return {
        "status": "success",
        "insights": {
            "local_search_impressions": {
                "value": "+22%",
                "label": "Local Search Impressions",
                "trend": "up",
            },
            "maps_visibility": {
                "value": "High",
                "label": "Google Maps Visibility",
                "area": "Campbelltown / Macarthur",
            },
            "pending_review_requests": {"value": 3, "label": "Pending Review Requests"},
            "gbp_posts_this_month": {"value": 0, "label": "GBP Posts This Month"},
            "note": "Impressions data is simulated for demo. Connect Google Search Console for live data.",
        },
    }


@router.post("/api/blog/startup-story")
async def generate_startup_story(data: dict):
    try:
        from services.agentic_rag import NarrativeBlogGenerator

        generator = NarrativeBlogGenerator()
        company_name = data.get("company_name", "")
        theme = data.get("theme", "entrepreneurship")

        result = generator.generate_blog_post(
            title=f"The {company_name} Story" if company_name else "Our Journey",
            theme=theme,
            company_name=company_name,
        )

        if result.get("status") == "error":
            return {"error": result.get("message", "Generation failed")}

        return {
            "title": result.get("title", "Untitled"),
            "content": result.get("content", ""),
            "company": company_name,
            "style": result.get("style", "wine_commercial_narrative"),
            "created_at": result.get("created_at", datetime.now().isoformat()),
        }
    except Exception as e:
        logger.error(f"Error generating startup story: {e}")
        return {"error": str(e)}
