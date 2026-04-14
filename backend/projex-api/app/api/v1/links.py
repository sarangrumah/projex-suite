"""Work item link API — create/list dependencies between items."""

from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.models.work_item import WorkItem
from app.models.work_item_link import WorkItemLink

router = APIRouter(tags=["links"])

VALID_LINK_TYPES = {"blocks", "is_blocked_by", "relates_to", "duplicates", "is_duplicated_by"}
INVERSE_LINKS = {
    "blocks": "is_blocked_by", "is_blocked_by": "blocks",
    "duplicates": "is_duplicated_by", "is_duplicated_by": "duplicates",
    "relates_to": "relates_to",
}


class LinkCreate(BaseModel):
    model_config = ConfigDict()
    target_key: str = Field(..., min_length=1)
    link_type: str = Field(..., pattern=r"^(blocks|is_blocked_by|relates_to|duplicates|is_duplicated_by)$")


@router.post("/items/{item_key}/links", status_code=201)
async def create_link(
    item_key: str, request: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    source = await _get_item(db, item_key)
    target = await _get_item(db, request.target_key)

    if source.id == target.id:
        raise HTTPException(status_code=400, detail="Cannot link an item to itself")

    # Check duplicate
    existing = await db.execute(
        select(WorkItemLink).where(
            WorkItemLink.source_id == source.id, WorkItemLink.target_id == target.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Link already exists")

    link = WorkItemLink(
        source_id=source.id, target_id=target.id,
        link_type=request.link_type, created_by=UUID(current_user["sub"]),
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return {
        "data": {
            "id": str(link.id), "source_key": item_key.upper(),
            "target_key": request.target_key.upper(), "link_type": link.link_type,
        },
        "meta": {}, "errors": [],
    }


@router.get("/items/{item_key}/links")
async def list_links(
    item_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    item = await _get_item(db, item_key)

    result = await db.execute(
        select(WorkItemLink).where(
            or_(WorkItemLink.source_id == item.id, WorkItemLink.target_id == item.id)
        )
    )
    links = list(result.scalars().all())

    data = []
    for link in links:
        # Determine direction
        if link.source_id == item.id:
            other_result = await db.execute(select(WorkItem).where(WorkItem.id == link.target_id))
            other = other_result.scalar_one_or_none()
            data.append({
                "id": str(link.id), "direction": "outward",
                "link_type": link.link_type,
                "item_key": other.key if other else "?",
                "item_title": other.title if other else "?",
            })
        else:
            other_result = await db.execute(select(WorkItem).where(WorkItem.id == link.source_id))
            other = other_result.scalar_one_or_none()
            inverse = INVERSE_LINKS.get(link.link_type, link.link_type)
            data.append({
                "id": str(link.id), "direction": "inward",
                "link_type": inverse,
                "item_key": other.key if other else "?",
                "item_title": other.title if other else "?",
            })

    return {"data": data, "meta": {"total": len(data)}, "errors": []}


@router.delete("/links/{link_id}")
async def delete_link(
    link_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(WorkItemLink).where(WorkItemLink.id == UUID(link_id)))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await db.delete(link)
    await db.commit()
    return {"data": {"deleted": True}, "meta": {}, "errors": []}


async def _get_item(db: AsyncSession, key: str) -> WorkItem:
    result = await db.execute(select(WorkItem).where(WorkItem.key == key.upper()))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{key}' not found")
    return item
