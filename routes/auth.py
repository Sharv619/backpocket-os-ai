"""
BackPocket OS — Auth routes (EPIC F)

POST /auth/register  — create new user
POST /auth/token     — login, returns JWT
GET  /auth/me        — return current user from token
"""

import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr

from services.auth import (
    AuthUser,
    TokenResponse,
    authenticate_user,
    create_user,
    get_current_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request bodies ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Create new BackPocket account via Supabase Auth."""
    result = create_user(body.email, body.password)
    return {
        "status": "success",
        "message": "Account created. Check email to confirm.",
        **result,
    }


@router.post("/token", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Authenticate user. Returns JWT access token for use in Authorization: Bearer header."""
    return authenticate_user(body.email, body.password)


@router.get("/me", response_model=AuthUser)
async def me(current_user: AuthUser = Depends(get_current_user)):
    """Return authenticated user details from token."""
    return current_user
