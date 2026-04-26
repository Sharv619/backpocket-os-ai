import sys
import io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except Exception:
        pass

import logging
from collections import deque

# In-memory ring buffer — last 150 log lines, exposed via /api/agentic-rag/logs
class _PipelineLogHandler(logging.Handler):
    def __init__(self, maxlen=150):
        super().__init__()
        self._buf = deque(maxlen=maxlen)

    def emit(self, record):
        from datetime import datetime
        self._buf.appendleft({
            "ts": datetime.now().strftime("%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        })

    def snapshot(self):
        return list(self._buf)

pipeline_log_handler = _PipelineLogHandler()
pipeline_log_handler.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.getLogger().addHandler(pipeline_log_handler)

import os
import asyncio
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ruff: noqa: E402
import services.database as db

db.init_db()

app = FastAPI(title="BackPocket Twin API")
logger.info("BACKPOCKET TWIN VERSION 2.2 STARTED")

# CORS — allow LAN origins + any configured ngrok/frontend URL
_LAN_ORIGINS = [
    f"http://{h}:{p}"
    for h in ["localhost", "127.0.0.1", "192.168.1.147"]
    for p in [3000, 8000, 8080, 40243]
]
_ngrok_url = os.getenv("NGROK_URL", "").rstrip("/")
_frontend_url = os.getenv("FRONTEND_ORIGIN", "")
_ALLOWED_ORIGINS = _LAN_ORIGINS + [u for u in [_ngrok_url, _frontend_url] if u]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS if _ALLOWED_ORIGINS else ["*"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── JWT / Auth Middleware ────────────────────────────────────────────────────
# Routes that do NOT require authentication
_PUBLIC_PATHS = {
    "/",
    "/health",
    "/login",
    "/auth/register",
    "/auth/token",
    "/auth/me",         # handled by its own Depends
    "/api/webhook",
    "/api/billing/webhook",
    "/test-sheets",
    "/test-whatsapp",
    "/self-check",
}
_PUBLIC_PREFIXES = ("/static/", "/app/", "/docs", "/openapi")

_BP_API_KEY = os.getenv("BP_API_KEY", "")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT-based auth gate for all /api/* routes.
    Bypass order:
      1. Public paths / prefixes — pass through.
      2. Supabase JWT present → verify + attach user to request state.
      3. X-API-Key fallback (dev/demo, or Flutter before Supabase wired) — only when
         SUPABASE_JWT_SECRET is unset. Removed once auth is fully live.
    """

    async def dispatch(self, request: StarletteRequest, call_next):
        path = request.url.path

        # Always pass public routes
        if path in _PUBLIC_PATHS:
            return await call_next(request)
        for prefix in _PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Only gate /api/* and /admin/api/* paths
        if not path.startswith("/api/") and not path.startswith("/admin/api/"):
            return await call_next(request)

        from services.auth import SUPABASE_JWT_SECRET, verify_jwt

        # --- JWT path ---
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and SUPABASE_JWT_SECRET:
            token = auth_header[len("Bearer "):]
            try:
                payload = verify_jwt(token)
                request.state.user_id = payload.get("sub", "")
                request.state.user_email = payload.get("email", "")
            except Exception:
                return StarletteResponse(
                    content='{"detail":"Invalid or expired token"}',
                    status_code=401,
                    media_type="application/json",
                )
            return await call_next(request)

        # --- X-API-Key fallback (dev / pre-Supabase Flutter clients) ---
        # Also accepts ?api_key=xxx query param so phone browsers can use a bookmarked URL
        if _BP_API_KEY:
            key = request.headers.get("x-api-key", "") or request.query_params.get("api_key", "")
            if key == _BP_API_KEY:
                request.state.user_id = "api-key-user"
                request.state.user_email = "apikey@backpocket.local"
                return await call_next(request)

        # --- No valid credential ---
        # If neither Supabase nor API key is configured, allow (local dev, no .env)
        if not SUPABASE_JWT_SECRET and not _BP_API_KEY:
            return await call_next(request)

        return StarletteResponse(
            content='{"detail":"Authentication required"}',
            status_code=401,
            media_type="application/json",
        )


app.add_middleware(AuthMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback

    error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR on {request.url.path}: {str(exc)}\n{traceback.format_exc()}\n---\n"
    logger.error(error_msg)
    try:
        with open("docs/ERROR_LOG.md", "a", encoding="utf-8") as f:
            f.write(error_msg)
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error. Logged to docs/ERROR_LOG.md.",
        },
    )


try:
    from services.session_manager import init_session_db

    init_session_db()
    logger.info("Session DB initialized")
except Exception as e:
    logger.warning(f"Session DB init skipped: {e}")

for _dir in ["static", "logs", "docs"]:
    if not os.path.exists(_dir):
        os.makedirs(_dir)

@app.middleware("http")
async def disable_cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/app"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")
# Flutter web app — built assets copied here by CI/CD
import os as _os
_flutter_dist = _os.path.join(_os.path.dirname(__file__), "static_flutter")
if _os.path.isdir(_flutter_dist):
    app.mount("/app", StaticFiles(directory=_flutter_dist, html=True), name="flutter")

# Route registration
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.voice import router as voice_router
from routes.construction import router as construction_router
from routes.mobile import router as mobile_router
from routes.documents import router as documents_router
from routes.voice_commands import router as voice_commands_router
from routes.email import router as email_router
from routes.chat import router as chat_router
from routes.instructions import router as instructions_router
from routes.integrations import router as integrations_router
from routes.marketing import router as marketing_router
from routes.utilities import router as utilities_router
from routes.approvals import router as approvals_router
from routes.webhook import router as webhook_router
from routes.billing import router as billing_router
from routes.compliance import router as compliance_router
from routes.byok import router as byok_router
from routes.ux_audit import router as ux_audit_router


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(voice_router)
app.include_router(construction_router)
app.include_router(mobile_router)
app.include_router(documents_router)
app.include_router(voice_commands_router)
app.include_router(email_router)
app.include_router(chat_router)
app.include_router(instructions_router)
app.include_router(integrations_router)
app.include_router(marketing_router)
app.include_router(utilities_router)
app.include_router(approvals_router)
app.include_router(webhook_router)
app.include_router(billing_router)
app.include_router(compliance_router)
app.include_router(byok_router)
app.include_router(ux_audit_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    from services.background import inbox_polling_loop
    asyncio.create_task(inbox_polling_loop())
    logger.info("🚀 Background polling loop started automatically")

@app.get("/")
async def root():
    return {"message": "BackPocket OS API is running. See /docs for details."}


@app.get("/login", include_in_schema=False)
async def login_page():
    return FileResponse("static/login.html")


@app.get("/run-poll")
async def run_poll():
    from services.background import inbox_polling_loop_once

    asyncio.create_task(inbox_polling_loop_once())
    return {"message": "Manual poll started."}


@app.get("/test-buttons")
async def test_buttons():
    from services.whapi import whatsapp_service

    founder_phone = "".join(filter(str.isdigit, os.getenv("FOUNDER_PHONE", "")))
    if not founder_phone:
        return {"status": "error", "message": "FOUNDER_PHONE not set"}

    test_text = "BACKPOCKET TWIN: BUTTON TEST\n\nIf you see these buttons, click one to verify it works!"
    buttons = [
        {"id": "test_approve", "title": "Approve"},
        {"id": "test_revise", "title": "Revise"},
        {"id": "self_check", "title": "Self-Check"},
    ]
    res = whatsapp_service.send_buttons(founder_phone, test_text, buttons)
    return {"status": "success", "whapi_response": res}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("BP_HOST", "0.0.0.0"),
        port=int(os.getenv("BP_PORT", "8000")),
        reload=False,
        use_colors=False,
        log_level="warning",
    )
