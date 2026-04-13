"""Auth API endpoints: register, login, refresh, MFA, logout, me."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MFAVerifyRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services.auth_service import AuthService
from app.core.security import decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new user account in the specified tenant."""
    service = AuthService(db)
    try:
        user, tokens = await service.register(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "mfa_enabled": user.mfa_enabled,
            },
            "tokens": tokens.model_dump(),
        },
        "meta": {},
        "errors": [],
    }


@router.post("/login")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate with email + password. Returns JWT pair."""
    service = AuthService(db)
    try:
        user, tokens, requires_mfa = await service.login(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    response_data = {
        "tokens": tokens.model_dump(),
        "requires_mfa": requires_mfa,
    }
    if not requires_mfa:
        response_data["user"] = {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "mfa_enabled": user.mfa_enabled,
        }

    return {"data": response_data, "meta": {}, "errors": []}


@router.post("/refresh")
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh access token using a valid refresh token."""
    try:
        payload = decode_token(request.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    service = AuthService(db)
    try:
        tokens = await service.refresh_tokens(payload["sub"], payload["tenant_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return {"data": {"tokens": tokens.model_dump()}, "meta": {}, "errors": []}


@router.post("/mfa/setup")
async def mfa_setup(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Generate TOTP secret and QR URI for MFA enrollment."""
    service = AuthService(db)
    try:
        result = await service.setup_mfa(UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"data": result.model_dump(), "meta": {}, "errors": []}


@router.post("/mfa/verify")
async def mfa_verify(
    request: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Verify TOTP code to complete MFA setup or login."""
    service = AuthService(db)
    try:
        valid = await service.verify_mfa(UUID(current_user["sub"]), request.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code",
        )

    return {"data": {"verified": True}, "meta": {}, "errors": []}


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Invalidate the current session / refresh token."""
    # In a production system, we'd add the refresh token JTI to a Redis blacklist.
    # For now, the client discards tokens and the short access TTL (15min) limits exposure.
    return {"data": {"logged_out": True}, "meta": {}, "errors": []}


@router.get("/me")
async def me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current user profile and permissions."""
    service = AuthService(db)
    try:
        user = await service.get_profile(UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "data": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "mfa_enabled": user.mfa_enabled,
            "permissions": current_user.get("permissions", []),
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }
