import asyncio
import functools
import logging
import sqlite3
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from app.models.schemas import GBPPostRequest

logger = logging.getLogger(__name__)
router = APIRouter()

DB = "backpocket.db"


def _init_marketing_table():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS marketing_activity (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            platform        TEXT NOT NULL DEFAULT 'gbp',
            activity_type   TEXT,
            job_description TEXT,
            suburb          TEXT,
            generated_post  TEXT,
            hashtags        TEXT,
            status          TEXT DEFAULT 'draft',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Add platform column if missing (migration for existing DBs)
    cols = [r[1] for r in con.execute("PRAGMA table_info(marketing_activity)").fetchall()]
    if cols and "platform" not in cols:
        con.execute("ALTER TABLE marketing_activity ADD COLUMN platform TEXT DEFAULT 'gbp'")
    if cols and "hashtags" not in cols:
        con.execute("ALTER TABLE marketing_activity ADD COLUMN hashtags TEXT")
    con.commit()
    con.close()


_init_marketing_table()


def _init_blog_posts_table():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            theme       TEXT,
            company     TEXT,
            content     TEXT NOT NULL,
            style       TEXT,
            source      TEXT DEFAULT 'blog_generator',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()


_init_blog_posts_table()


class SocialPostRequest(BaseModel):
    job_description: str
    suburb: str
    outcome: str = ""
    before_after: bool = False


def _fetch_past_gbp_posts(job_description: str, suburb: str, n: int = 3) -> list[dict]:
    """Pull recent successful GBP posts as few-shot examples.

    Prefers posts from the same suburb, falls back to any recent posts.
    No embeddings needed at this scale — SQL is sufficient.
    """
    try:
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Try suburb match first
        cur.execute(
            """SELECT job_description, suburb, generated_post FROM marketing_activity
               WHERE platform = 'gbp' AND generated_post IS NOT NULL
               AND suburb LIKE ? ORDER BY created_at DESC LIMIT ?""",
            (f"%{suburb}%", n),
        )
        rows = cur.fetchall()
        if len(rows) < n:
            # Pad with any recent posts
            cur.execute(
                """SELECT job_description, suburb, generated_post FROM marketing_activity
                   WHERE platform = 'gbp' AND generated_post IS NOT NULL
                   ORDER BY created_at DESC LIMIT ?""",
                (n,),
            )
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows[:n]]
    except Exception:
        return []


@router.post("/api/marketing/gbp-post")
async def create_gbp_post(request: GBPPostRequest):
    try:
        from services.gemini import get_openrouter_response, get_gemini_client

        # Few-shot: pull past posts as examples so AI matches proven style
        examples = _fetch_past_gbp_posts(request.job_description, request.suburb)
        few_shot = ""
        if examples:
            few_shot = "\n\nHere are examples of past posts that performed well:\n"
            for ex in examples:
                few_shot += f'- Job: {ex["job_description"]}, Suburb: {ex["suburb"]}\n  Post: {ex["generated_post"]}\n'
            few_shot += "\nMatch the tone, length, and local feel of those examples.\n"

        prompt = (
            f"Write a 2-sentence Google Business Profile post for a tradie business "
            f"in {request.suburb}, Australia. "
            f"The job was: {request.job_description}. "
            f"Tone: friendly, local, professional. Mention the suburb. "
            f"End with a call-to-action like 'Call us for a free quote!'"
            f"{few_shot}"
            f"\nReturn ONLY the post text, no quotes or labels."
        )

        post_text = None

        client = get_gemini_client()
        if client:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            post_text = response.text.strip() if response and response.text else None

        if not post_text:
            post_text = get_openrouter_response(
                prompt,
                model="google/gemini-2.5-flash",
                sys_prompt="You are a local tradie marketing assistant. Write punchy, local GBP posts.",
            )

        if not post_text:
            post_text = (
                f"Just completed a job in {request.suburb}! "
                f"{request.job_description} - done right, on time. "
                f"Call us for a free quote!"
            )

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO marketing_activity
               (platform, activity_type, job_description, suburb, generated_post, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("gbp", "gbp_post", request.job_description, request.suburb, post_text, "draft"),
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
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
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


def _ai_generate(prompt: str, sys_prompt: str, fallback: str) -> str:
    """Shared AI generation with Gemini → OpenRouter → static fallback."""
    from services.gemini import get_openrouter_response, get_gemini_client
    text = None
    client = get_gemini_client()
    if client:
        try:
            r = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = r.text.strip() if r and r.text else None
        except Exception:
            pass
    if not text:
        text = get_openrouter_response(
            prompt,
            model="google/gemini-2.5-flash",
            sys_prompt=sys_prompt,
        )
    return text or fallback


def _save_post(platform: str, activity_type: str, job_description: str, suburb: str, post: str, hashtags: str = "") -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO marketing_activity (platform, activity_type, job_description, suburb, generated_post, hashtags, status) VALUES (?,?,?,?,?,?,?)",
        (platform, activity_type, job_description, suburb, post, hashtags, "draft"),
    )
    aid = cur.lastrowid
    con.commit()
    con.close()
    return aid


def _save_blog_post(
    title: str,
    content: str,
    theme: str = "",
    company: str = "",
    style: str = "wine_commercial_narrative",
    source: str = "blog_generator",
) -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        """INSERT INTO blog_posts (title, theme, company, content, style, source)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, theme, company, content, style, source),
    )
    post_id = cur.lastrowid
    con.commit()
    con.close()
    return post_id


@router.post("/api/marketing/facebook-post")
async def create_facebook_post(request: SocialPostRequest):
    """Generate a Facebook post (80-120 words) for a completed tradie job."""
    try:
        outcome_line = f" The result: {request.outcome}." if request.outcome else ""
        before_after_line = " Include a before/after mention." if request.before_after else ""
        prompt = (
            f"Write a Facebook post (80-120 words) for a tradie business in {request.suburb}, Australia. "
            f"The job was: {request.job_description}.{outcome_line}{before_after_line} "
            f"Tone: warm, proud, local. Mention the suburb naturally. "
            f"End with a call-to-action (free quote, DM us, etc). "
            f"Return ONLY the post text, no labels or hashtags."
        )
        fallback = (
            f"Another job done right in {request.suburb}! "
            f"We just finished {request.job_description} and the client couldn't be happier. "
            f"If you need quality tradie work in the area, give us a call for a free quote!"
        )
        post = _ai_generate(prompt, "You are a tradie social media manager. Write engaging Facebook posts.", fallback)
        aid = _save_post("facebook", "facebook_post", request.job_description, request.suburb, post)
        return {"status": "success", "activity_id": aid, "platform": "facebook", "post": post}
    except Exception as e:
        logger.error(f"Facebook post error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/api/marketing/instagram-caption")
async def create_instagram_caption(request: SocialPostRequest):
    """Generate an Instagram caption (30-50 words) + 5 relevant hashtags."""
    try:
        prompt = (
            f"Write an Instagram caption (30-50 words) for a tradie business in {request.suburb}, Australia. "
            f"The job was: {request.job_description}. "
            f"Tone: punchy, proud, visual. Mention the suburb. "
            f"Then on a new line write exactly 5 relevant hashtags (e.g. #tradie #sydney #plumbing). "
            f"Format: CAPTION\\nHASHTAGS"
        )
        fallback = f"Quality work in {request.suburb}. {request.job_description} — done right. 🔨\n#tradie #{request.suburb.lower().replace(' ','')} #aussietradie #qualitywork #localtradie"
        raw = _ai_generate(prompt, "You are a tradie Instagram manager. Write punchy captions with hashtags.", fallback)

        # Split caption from hashtags
        parts = raw.strip().split("\n")
        hashtag_line = next((p for p in reversed(parts) if p.strip().startswith("#")), "")
        caption_lines = [p for p in parts if not p.strip().startswith("#")]
        caption = " ".join(caption_lines).strip()
        hashtags = hashtag_line.strip()

        aid = _save_post("instagram", "instagram_caption", request.job_description, request.suburb, caption, hashtags)
        return {"status": "success", "activity_id": aid, "platform": "instagram", "caption": caption, "hashtags": hashtags}
    except Exception as e:
        logger.error(f"Instagram caption error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/api/blog/startup-story")
async def generate_startup_story(data: dict):
    try:
        from services.agentic_rag import NarrativeBlogGenerator

        company_name = data.get("company_name", "") or "BackPocket"
        theme = data.get("theme", "entrepreneurship")
        title = f"The {company_name} Story"

        generator = NarrativeBlogGenerator()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            functools.partial(
                generator.generate_blog_post,
                title=title,
                theme=theme,
                company_name=company_name,
            ),
        )

        if result.get("error"):
            return {"error": result["error"]}

        post_id = _save_blog_post(
            title=result.get("title", title),
            content=result.get("content", ""),
            theme=theme,
            company=company_name,
            style=result.get("style", "wine_commercial_narrative"),
            source="startup_story",
        )

        return {
            "id": post_id,
            "title": result.get("title", title),
            "content": result.get("content", ""),
            "company": company_name,
            "theme": theme,
            "style": result.get("style", "wine_commercial_narrative"),
            "created_at": result.get("created_at", datetime.now().isoformat()),
        }
    except Exception as e:
        logger.error(f"Error generating startup story: {e}")
        return {"error": str(e)}


@router.get("/api/blog/generate")
async def generate_blog_post(title: str, theme: str = "entrepreneurship"):
    try:
        from services.agentic_rag import get_blog_generator

        clean_title = title.strip() or "Untitled Story"
        clean_theme = theme.strip() or "entrepreneurship"

        generator = get_blog_generator()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            functools.partial(
                generator.generate_blog_post,
                title=clean_title,
                theme=clean_theme,
            ),
        )

        if result.get("error"):
            return {"error": result["error"]}

        post_id = _save_blog_post(
            title=result.get("title", clean_title),
            content=result.get("content", ""),
            theme=clean_theme,
            company=result.get("company", ""),
            style=result.get("style", "wine_commercial_narrative"),
            source="blog_post",
        )

        return {
            "id": post_id,
            "title": result.get("title", clean_title),
            "theme": clean_theme,
            "content": result.get("content", ""),
            "style": result.get("style", "wine_commercial_narrative"),
            "created_at": result.get("created_at", datetime.now().isoformat()),
        }
    except Exception as e:
        logger.error(f"Error generating blog post: {e}")
        return {"error": str(e)}


@router.get("/api/blog/library")
async def get_blog_library(limit: int = 30):
    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(
            """SELECT id, title, theme, company, content, style, source, created_at
               FROM blog_posts
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return {"items": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"Error loading blog library: {e}")
        return {"error": str(e), "items": [], "count": 0}
