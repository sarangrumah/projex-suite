"""Wiki API endpoints: CRUD + version history per space."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.schemas.wiki import WikiPageCreate, WikiPageUpdate
from app.services.wiki_service import WikiService

router = APIRouter(tags=["wiki"])


@router.post("/spaces/{space_key}/wiki", status_code=status.HTTP_201_CREATED)
async def create_page(
    space_key: str,
    request: WikiPageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.WIKI_CREATE)),
) -> dict:
    """Create a wiki page in the given space."""
    service = WikiService(db)
    try:
        page = await service.create(space_key.upper(), request, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(page.id),
            "title": page.title,
            "slug": page.slug,
            "body": page.body,
            "parent_id": str(page.parent_id) if page.parent_id else None,
            "position": page.position,
            "created_at": page.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.get("/spaces/{space_key}/wiki")
async def list_pages(
    space_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """List all wiki pages for a space."""
    service = WikiService(db)
    try:
        pages = await service.list(space_key.upper())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "data": [
            {
                "id": str(p.id),
                "parent_id": str(p.parent_id) if p.parent_id else None,
                "title": p.title,
                "slug": p.slug,
                "position": p.position,
                "updated_at": p.updated_at.isoformat(),
            }
            for p in pages
        ],
        "meta": {},
        "errors": [],
    }


@router.get("/wiki/{page_id}")
async def get_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get a wiki page with full body."""
    service = WikiService(db)
    page = await service.get(UUID(page_id))
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")

    return {
        "data": {
            "id": str(page.id),
            "title": page.title,
            "slug": page.slug,
            "body": page.body,
            "parent_id": str(page.parent_id) if page.parent_id else None,
            "position": page.position,
            "created_by": str(page.created_by),
            "updated_by": str(page.updated_by) if page.updated_by else None,
            "created_at": page.created_at.isoformat(),
            "updated_at": page.updated_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.put("/wiki/{page_id}")
async def update_page(
    page_id: str,
    request: WikiPageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.WIKI_EDIT)),
) -> dict:
    """Update a wiki page. Creates a version snapshot if content changed."""
    service = WikiService(db)
    try:
        page = await service.update(UUID(page_id), request, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(page.id),
            "title": page.title,
            "slug": page.slug,
            "body": page.body,
            "updated_at": page.updated_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.delete("/wiki/{page_id}")
async def delete_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    """Delete a wiki page and its version history. Admin only."""
    service = WikiService(db)
    try:
        await service.delete(UUID(page_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {"data": {"deleted": True}, "meta": {}, "errors": []}


@router.get("/wiki/{page_id}/versions")
async def list_versions(
    page_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get version history for a wiki page."""
    service = WikiService(db)
    versions = await service.get_versions(UUID(page_id))

    return {
        "data": [
            {
                "id": str(v.id),
                "version_num": v.version_num,
                "title": v.title,
                "edited_by": str(v.edited_by),
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ],
        "meta": {},
        "errors": [],
    }
