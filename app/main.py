import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

from app.core.config import logger
from app.core.middleware import APIKeyMiddleware, setup_cors
from app.models.schemas import LogRequest

load_dotenv()

app = FastAPI(title="BackPocket Twin API")
logger.info("BACKPOCKET TWIN VERSION 2.2 STARTED")

setup_cors(app)
app.add_middleware(APIKeyMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    from datetime import datetime

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

from routes.admin import router as admin_router
from routes.voice import router as voice_router
from routes.construction import router as construction_router
from routes.mobile import router as mobile_router
from routes.documents import router as documents_router
from routes.voice_commands import router as voice_commands_router


app.include_router(admin_router)
app.include_router(voice_router)
app.include_router(construction_router)
app.include_router(mobile_router)
app.include_router(documents_router)
app.include_router(voice_commands_router)


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


@app.post("/api/dev/auto-log")
async def api_auto_log(request: LogRequest):
    from datetime import datetime

    try:
        date_str = datetime.now().strftime("%b %d, %Y")
        entry = f"\n### Auto-Log Date: {date_str}\n{request.content}\n"

        file_path = (
            "SESSION_LOG.md" if request.log_type == "session" else "docs/JOURNEY.md"
        )
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return {"status": "success", "file": file_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/static/index.html")
async def get_index():
    import hashlib

    file_path = "static/index.html"
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
    else:
        file_hash = "unknown"
    return FileResponse(
        file_path,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-File-Version": file_hash,
        },
    )
