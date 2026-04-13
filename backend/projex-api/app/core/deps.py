"""FastAPI dependencies: DB session, current user, tenant, permissions."""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, set_tenant_schema
from app.core.security import decode_token

security_scheme = HTTPBearer()


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session with tenant schema set from request state."""
    async with async_session_factory() as session:
        tenant_slug = getattr(request.state, "tenant_slug", None)
        if tenant_slug:
            await set_tenant_schema(session, tenant_slug)
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict[str, Any]:
    """Extract and validate user from JWT Bearer token.

    Returns the decoded token payload containing:
    sub, tenant_id, role, permissions, device_fingerprint
    """
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cannot use refresh token for API access",
        )

    return payload


def require_permission(permission: str):
    """Dependency factory: check that the current user has a specific permission."""

    async def _check(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_role = current_user.get("role", "")
        user_permissions = current_user.get("permissions", [])

        # Admin bypasses all permission checks
        if user_role == "admin":
            return current_user

        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return Depends(_check)
