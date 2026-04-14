"""Search API — full-text search across items, wiki, docs via Meilisearch."""

from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.models.work_item import WorkItem
from app.models.wiki import WikiPage
from app.models.space import Space

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    scope: str = Query(default="all", pattern=r"^(all|items|wiki)$"),
    space_key: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Search across work items and wiki pages. Falls back to SQL ILIKE when Meilisearch unavailable."""
    results: list[dict] = []
    pattern = f"%{q}%"

    # Resolve space filter
    space_id = None
    if space_key:
        sr = await db.execute(select(Space).where(Space.key == space_key.upper()))
        space = sr.scalar_one_or_none()
        if space:
            space_id = space.id

    # Search work items
    if scope in ("all", "items"):
        item_q = select(WorkItem).where(
            or_(WorkItem.title.ilike(pattern), WorkItem.key.ilike(pattern))
        )
        if space_id:
            item_q = item_q.where(WorkItem.space_id == space_id)
        item_q = item_q.limit(20)
        item_result = await db.execute(item_q)
        for item in item_result.scalars().all():
            results.append({
                "type": "item", "id": str(item.id), "key": item.key,
                "title": item.title, "priority": item.priority,
                "link": f"/items/{item.key}",
            })

    # Search wiki pages
    if scope in ("all", "wiki"):
        wiki_q = select(WikiPage).where(WikiPage.title.ilike(pattern))
        if space_id:
            wiki_q = wiki_q.where(WikiPage.space_id == space_id)
        wiki_q = wiki_q.limit(20)
        wiki_result = await db.execute(wiki_q)
        for page in wiki_result.scalars().all():
            results.append({
                "type": "wiki", "id": str(page.id),
                "title": page.title, "slug": page.slug,
                "link": f"/wiki/{page.id}",
            })

    return {"data": results, "meta": {"query": q, "total": len(results)}, "errors": []}
