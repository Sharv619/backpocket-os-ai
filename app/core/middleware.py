import os
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

_BP_API_KEY = os.getenv("BP_API_KEY", "")


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if not _BP_API_KEY:
            return await call_next(request)
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        key = request.headers.get("x-api-key", "")
        if key != _BP_API_KEY:
            return StarletteResponse(
                content='{"detail":"Invalid or missing X-API-Key"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


def setup_cors(app):
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
