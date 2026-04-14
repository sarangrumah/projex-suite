"""Automations API — CRUD for when-trigger rules."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.models.automation import Automation
from app.models.space import Space

router = APIRouter(tags=["automations"])

TRIGGER_TYPES = {"status_changed", "item_created", "item_assigned", "due_date_passed", "sprint_started", "sprint_closed"}
ACTION_TYPES = {"assign_user", "change_status", "send_notification", "add_comment", "move_to_sprint", "webhook"}


class AutomationCreate(BaseModel):
    model_config = ConfigDict()
    name: str = Field(..., min_length=1, max_length=255)
    trigger_type: str
    trigger_config: dict = Field(default_factory=dict)
    action_type: str
    action_config: dict = Field(default_factory=dict)


class AutomationUpdate(BaseModel):
    model_config = ConfigDict()
    name: str | None = None
    is_active: bool | None = None
    trigger_config: dict | None = None
    action_config: dict | None = None


@router.post("/spaces/{space_key}/automations", status_code=201)
async def create_automation(
    space_key: str, request: AutomationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    if request.trigger_type not in TRIGGER_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid trigger_type. Must be one of: {', '.join(TRIGGER_TYPES)}")
    if request.action_type not in ACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid action_type. Must be one of: {', '.join(ACTION_TYPES)}")

    result = await db.execute(select(Space).where(Space.key == space_key.upper()))
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    auto = Automation(
        space_id=space.id, name=request.name,
        trigger_type=request.trigger_type, trigger_config=request.trigger_config,
        action_type=request.action_type, action_config=request.action_config,
        created_by=UUID(current_user["sub"]),
    )
    db.add(auto)
    await db.commit()
    await db.refresh(auto)
    return {"data": _auto_dict(auto), "meta": {}, "errors": []}


@router.get("/spaces/{space_key}/automations")
async def list_automations(
    space_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(Space).where(Space.key == space_key.upper()))
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    autos = await db.execute(
        select(Automation).where(Automation.space_id == space.id).order_by(Automation.created_at)
    )
    return {"data": [_auto_dict(a) for a in autos.scalars().all()], "meta": {}, "errors": []}


@router.put("/automations/{auto_id}")
async def update_automation(
    auto_id: str, request: AutomationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    result = await db.execute(select(Automation).where(Automation.id == UUID(auto_id)))
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    for k, v in request.model_dump(exclude_unset=True).items():
        setattr(auto, k, v)
    await db.commit()
    await db.refresh(auto)
    return {"data": _auto_dict(auto), "meta": {}, "errors": []}


@router.delete("/automations/{auto_id}")
async def delete_automation(
    auto_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    result = await db.execute(select(Automation).where(Automation.id == UUID(auto_id)))
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    await db.delete(auto)
    await db.commit()
    return {"data": {"deleted": True}, "meta": {}, "errors": []}


def _auto_dict(a: Automation) -> dict:
    return {
        "id": str(a.id), "name": a.name, "is_active": a.is_active,
        "trigger_type": a.trigger_type, "trigger_config": a.trigger_config,
        "action_type": a.action_type, "action_config": a.action_config,
        "created_at": a.created_at.isoformat(),
    }
