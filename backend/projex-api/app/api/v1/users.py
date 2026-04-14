"""User management API — admin endpoints for listing, updating, deactivating users."""

from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.models.user import User

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


class UserUpdate(BaseModel):
    model_config = ConfigDict()
    display_name: str | None = None
    role: str | None = Field(default=None, pattern=r"^(admin|member|viewer|guest)$")
    is_active: bool | None = None


@router.get("/")
async def list_users(
    page: int = 1, per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_USERS)),
) -> dict:
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = list(result.scalars().all())
    total = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    return {
        "data": [_user_dict(u) for u in users],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "errors": [],
    }


@router.get("/{user_id}")
async def get_user(
    user_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_USERS)),
) -> dict:
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"data": _user_dict(user), "meta": {}, "errors": []}


@router.put("/{user_id}")
async def update_user(
    user_id: str, request: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_USERS)),
) -> dict:
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deactivating yourself
    if request.is_active is False and str(user.id) == current_user["sub"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    for k, v in request.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return {"data": _user_dict(user), "meta": {}, "errors": []}


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_USERS)),
) -> dict:
    if user_id == current_user["sub"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"data": {"deactivated": True}, "meta": {}, "errors": []}


def _user_dict(u: User) -> dict:
    return {
        "id": str(u.id), "email": u.email, "display_name": u.display_name,
        "role": u.role, "mfa_enabled": u.mfa_enabled, "is_active": u.is_active,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat(),
    }
