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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

import os
import asyncio
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
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

# CORS
_LAN_ORIGINS = [
    f"http://{h}:{p}"
    for h in ["localhost", "127.0.0.1", "192.168.1.147"]
    for p in [3000, 8000, 8080, 40243]
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):\d+$",
    allow_origins=[o for o in _LAN_ORIGINS + [os.getenv("FRONTEND_ORIGIN", "")] if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── JWT / Auth Middleware ────────────────────────────────────────────────────
# Routes that do NOT require authentication
_PUBLIC_PATHS = {
    "/",
    "/health",
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

        # Only gate /api/* paths
        if not path.startswith("/api/"):
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
        if _BP_API_KEY:
            key = request.headers.get("x-api-key", "")
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

import routes.voice_handlers_dashboard
import routes.voice_handlers_inbox
import routes.voice_handlers_construction
import routes.voice_handlers_misc
import routes.voice_handlers_cross

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


@app.on_event("startup")
async def startup_event():
    pass


@app.get("/dashboard")
async def get_dashboard():
    return FileResponse(
        "static/index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


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
