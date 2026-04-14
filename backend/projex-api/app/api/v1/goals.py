"""Goals/OKR API endpoints."""

from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.schemas.goal import GoalCreate, GoalUpdate, KeyResultCreate, KeyResultUpdate
from app.services.goal_service import GoalService

router = APIRouter(tags=["goals"])


@router.post("/spaces/{space_key}/goals", status_code=status.HTTP_201_CREATED)
async def create_goal(
    space_key: str, request: GoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = GoalService(db)
    try:
        g = await service.create_goal(space_key.upper(), request, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _goal_dict(g), "meta": {}, "errors": []}


@router.get("/spaces/{space_key}/goals")
async def list_goals(
    space_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = GoalService(db)
    try:
        goals = await service.list_goals(space_key.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    result = []
    for g in goals:
        gd = _goal_dict(g)
        krs = await service.list_key_results(g.id)
        gd["key_results"] = [_kr_dict(kr) for kr in krs]
        result.append(gd)
    return {"data": result, "meta": {}, "errors": []}


@router.put("/goals/{goal_id}")
async def update_goal(
    goal_id: str, request: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = GoalService(db)
    try:
        g = await service.update_goal(UUID(goal_id), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _goal_dict(g), "meta": {}, "errors": []}


@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    service = GoalService(db)
    try:
        await service.delete_goal(UUID(goal_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": {"deleted": True}, "meta": {}, "errors": []}


@router.post("/goals/{goal_id}/key-results", status_code=status.HTTP_201_CREATED)
async def add_key_result(
    goal_id: str, request: KeyResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = GoalService(db)
    try:
        kr = await service.add_key_result(UUID(goal_id), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _kr_dict(kr), "meta": {}, "errors": []}


@router.put("/key-results/{kr_id}")
async def update_key_result(
    kr_id: str, request: KeyResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = GoalService(db)
    try:
        kr = await service.update_key_result(UUID(kr_id), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _kr_dict(kr), "meta": {}, "errors": []}


def _goal_dict(g) -> dict:  # noqa: ANN001
    return {
        "id": str(g.id), "title": g.title, "description": g.description,
        "status": g.status, "progress": g.progress,
        "start_date": g.start_date.isoformat() if g.start_date else None,
        "due_date": g.due_date.isoformat() if g.due_date else None,
        "owner_id": str(g.owner_id), "created_at": g.created_at.isoformat(),
    }

def _kr_dict(kr) -> dict:  # noqa: ANN001
    progress = 0.0
    rng = kr.target_value - kr.start_value
    if rng > 0:
        progress = min(((kr.current_value - kr.start_value) / rng) * 100, 100)
    return {
        "id": str(kr.id), "title": kr.title, "metric_type": kr.metric_type,
        "current_value": kr.current_value, "target_value": kr.target_value,
        "start_value": kr.start_value, "unit": kr.unit,
        "progress": round(progress, 1),
    }
