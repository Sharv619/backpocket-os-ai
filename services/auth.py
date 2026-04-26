"""
BackPocket OS — Auth service (EPIC F)

Supabase-backed user management + JWT verification.
Falls back to BP_API_KEY bypass when SUPABASE_JWT_SECRET is unset (dev/demo).
"""

import os
import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SUPABASE_URL        = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY   = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")  # Settings → API → JWT secret
_BP_API_KEY         = os.getenv("BP_API_KEY", "")

_JWT_ALGORITHM = "HS256"
_JWT_AUDIENCE  = "authenticated"

# ── Models ────────────────────────────────────────────────────────────────────

class AuthUser(BaseModel):
    id: str
    email: str
    role: str = "authenticated"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


# ── supabase_auth client (lazy init) ──────────────────────────────────────────
# supabase_auth is the successor to gotrue-py — auth-only, no storage3/pyiceberg.

_auth_client = None


def _client():
    global _auth_client
    if _auth_client is not None:
        return _auth_client
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env"
        )
    from supabase_auth import SyncGoTrueClient
    _auth_client = SyncGoTrueClient(
        url=f"{SUPABASE_URL.rstrip('/')}/auth/v1",
        headers={"apikey": SUPABASE_ANON_KEY},
    )
    return _auth_client


# ── JWT verification ──────────────────────────────────────────────────────────

def verify_jwt(token: str) -> dict:
    """
    Decode + verify Supabase-issued JWT.
    Returns full payload dict on success, raises HTTP 401 on failure.
    """
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: SUPABASE_JWT_SECRET missing",
        )
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[_JWT_ALGORITHM],
            audience=_JWT_AUDIENCE,
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependency ────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None,
) -> AuthUser:
    """
    FastAPI dependency. Extracts Bearer JWT from Authorization header.
    Dev bypass: if SUPABASE_JWT_SECRET unset and BP_API_KEY matches X-API-Key header
    or ?api_key= query param, returns stub admin user.
    """
    # Dev/demo bypass — allows existing Flutter clients to work before Supabase is wired
    if not SUPABASE_JWT_SECRET and _BP_API_KEY:
        api_key = (
            request.headers.get("x-api-key", "")
            or request.query_params.get("api_key", "")
        )
        if api_key == _BP_API_KEY:
            return AuthUser(id="dev-user", email="dev@backpocket.local", role="admin")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials (dev mode: provide X-API-Key or ?api_key=)",
        )

    # Production path — require Bearer JWT
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header[len("Bearer "):]
    payload = verify_jwt(token)

    user_id = payload.get("sub", "")
    email   = payload.get("email", "")
    # Check app_metadata first (admin-assigned role), then user_metadata, then JWT root claim
    app_meta  = payload.get("app_metadata") or {}
    user_meta = payload.get("user_metadata") or {}
    role = app_meta.get("role") or user_meta.get("role") or payload.get("role", "authenticated")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    return AuthUser(id=user_id, email=email, role=role)


# ── User registration ─────────────────────────────────────────────────────────

def create_user(email: str, password: str) -> dict:
    """
    Register new user via Supabase Auth (GoTrue).
    Returns user dict on success. Raises HTTPException on failure.
    """
    _validate_password(password)
    try:
        from supabase_auth.types import SignUpWithPasswordCredentials
        resp = _client().sign_up(
            SignUpWithPasswordCredentials(email=email, password=password)
        )
        if resp.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed — check email or try again",
            )
        logger.info(f"New user registered: {email}")
        return {
            "user_id": resp.user.id,
            "email": resp.user.email,
            "confirmed": resp.user.email_confirmed_at is not None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── User login ────────────────────────────────────────────────────────────────

def authenticate_user(email: str, password: str) -> TokenResponse:
    """
    Authenticate user via Supabase Auth (GoTrue).
    Returns JWT access token on success.
    """
    try:
        from supabase_auth.types import SignInWithPasswordCredentials
        resp = _client().sign_in_with_password(
            SignInWithPasswordCredentials(email=email, password=password)
        )
        if resp.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return TokenResponse(
            access_token=resp.session.access_token,
            token_type="bearer",
            user_id=resp.user.id,
            email=resp.user.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


# ── Password validation ───────────────────────────────────────────────────────

def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )


# ── RBAC helper ───────────────────────────────────────────────────────────────

def require_role(*roles: str):
    """
    FastAPI dependency factory. Raises 403 if the authenticated user's role
    is not in the allowed set.

    Usage:
        @app.delete("/api/something")
        async def delete_it(user: AuthUser = Depends(require_role("admin"))):
            ...
    """
    from fastapi import Depends

    async def checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorised for this action. Required: {list(roles)}",
            )
        return user

    return checker


# ── Auth configured check (for health endpoint) ───────────────────────────────

def auth_is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_JWT_SECRET)
