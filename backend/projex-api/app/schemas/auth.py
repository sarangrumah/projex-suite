"""Pydantic v2 schemas for authentication endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Requests ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)
    tenant_slug: str = Field(..., min_length=2, max_length=63, pattern=r"^[a-z0-9\-]+$")


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    tenant_slug: str = Field(..., min_length=2, max_length=63)
    device_fingerprint: str | None = None


class RefreshRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    refresh_token: str


class MFASetupRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    pass  # No body needed — generates for current user


class MFAVerifyRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class LogoutRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    refresh_token: str | None = None


# ── Responses ───────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    avatar_url: str | None
    role: str
    mfa_enabled: bool
    is_active: bool
    created_at: datetime


class MFASetupResponse(BaseModel):
    secret: str
    qr_uri: str


class RegisterResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
