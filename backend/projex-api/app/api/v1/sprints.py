"""Sprint API endpoints — CRUD, start, close, backlog."""

from __future__ import annotations
from datetime import date, datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.models.sprint import Sprint
from app.models.space import Space
from app.models.work_item import WorkItem

router = APIRouter(tags=["sprints"])


class SprintCreate(BaseModel):
    model_config = ConfigDict()
    name: str = Field(..., min_length=1, max_length=127)
    goal: str | None = Field(default=None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None


class SprintUpdate(BaseModel):
    model_config = ConfigDict()
    name: str | None = None
    goal: str | None = None
    status: str | None = Field(default=None, pattern=r"^(planned|active|completed)$")
    start_date: date | None = None
    end_date: date | None = None


@router.post("/spaces/{space_key}/sprints", status_code=201)
async def create_sprint(
    space_key: str, request: SprintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.SPRINT_CREATE)),
) -> dict:
    space = await _get_space(db, space_key)
    sprint = Sprint(space_id=space.id, name=request.name, goal=request.goal,
                    start_date=request.start_date, end_date=request.end_date)
    db.add(sprint)
    await db.commit()
    await db.refresh(sprint)
    return {"data": _sprint_dict(sprint), "meta": {}, "errors": []}


@router.get("/spaces/{space_key}/sprints")
async def list_sprints(
    space_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    space = await _get_space(db, space_key)
    result = await db.execute(
        select(Sprint).where(Sprint.space_id == space.id).order_by(Sprint.created_at.desc())
    )
    sprints = list(result.scalars().all())
    data = []
    for s in sprints:
        sd = _sprint_dict(s)
        count = (await db.execute(
            select(func.count()).select_from(WorkItem).where(WorkItem.sprint_id == s.id)
        )).scalar() or 0
        sd["item_count"] = count
        data.append(sd)
    return {"data": data, "meta": {}, "errors": []}


@router.put("/sprints/{sprint_id}")
async def update_sprint(
    sprint_id: str, request: SprintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.SPRINT_CREATE)),
) -> dict:
    result = await db.execute(select(Sprint).where(Sprint.id == UUID(sprint_id)))
    sprint = result.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    for k, v in request.model_dump(exclude_unset=True).items():
        setattr(sprint, k, v)
    await db.commit()
    await db.refresh(sprint)
    return {"data": _sprint_dict(sprint), "meta": {}, "errors": []}


@router.post("/sprints/{sprint_id}/start")
async def start_sprint(
    sprint_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.SPRINT_START)),
) -> dict:
    result = await db.execute(select(Sprint).where(Sprint.id == UUID(sprint_id)))
    sprint = result.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if sprint.status != "planned":
        raise HTTPException(status_code=400, detail="Sprint must be in 'planned' status to start")
    sprint.status = "active"
    if not sprint.start_date:
        sprint.start_date = date.today()
    await db.commit()
    await db.refresh(sprint)
    return {"data": _sprint_dict(sprint), "meta": {}, "errors": []}


@router.post("/sprints/{sprint_id}/close")
async def close_sprint(
    sprint_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.SPRINT_CLOSE)),
) -> dict:
    result = await db.execute(select(Sprint).where(Sprint.id == UUID(sprint_id)))
    sprint = result.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if sprint.status != "active":
        raise HTTPException(status_code=400, detail="Sprint must be 'active' to close")
    sprint.status = "completed"
    if not sprint.end_date:
        sprint.end_date = date.today()
    await db.commit()
    await db.refresh(sprint)
    return {"data": _sprint_dict(sprint), "meta": {}, "errors": []}


@router.get("/sprints/{sprint_id}/items")
async def sprint_items(
    sprint_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(WorkItem).where(WorkItem.sprint_id == UUID(sprint_id)).order_by(WorkItem.position)
    )
    items = list(result.scalars().all())
    return {
        "data": [
            {"id": str(i.id), "key": i.key, "title": i.title, "type": i.type,
             "priority": i.priority, "status_id": str(i.status_id) if i.status_id else None}
            for i in items
        ],
        "meta": {"total": len(items)}, "errors": [],
    }


@router.get("/spaces/{space_key}/backlog")
async def backlog(
    space_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get items not assigned to any sprint."""
    space = await _get_space(db, space_key)
    result = await db.execute(
        select(WorkItem).where(WorkItem.space_id == space.id, WorkItem.sprint_id == None)  # noqa: E711
        .order_by(WorkItem.position)
    )
    items = list(result.scalars().all())
    return {
        "data": [
            {"id": str(i.id), "key": i.key, "title": i.title, "type": i.type,
             "priority": i.priority}
            for i in items
        ],
        "meta": {"total": len(items)}, "errors": [],
    }


async def _get_space(db: AsyncSession, key: str) -> Space:
    result = await db.execute(select(Space).where(Space.key == key.upper()))
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail=f"Space '{key}' not found")
    return space


def _sprint_dict(s: Sprint) -> dict:
    return {
        "id": str(s.id), "name": s.name, "goal": s.goal, "status": s.status,
        "start_date": s.start_date.isoformat() if s.start_date else None,
        "end_date": s.end_date.isoformat() if s.end_date else None,
        "created_at": s.created_at.isoformat(),
    }
