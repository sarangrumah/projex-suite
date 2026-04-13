"""Space API endpoints: CRUD with template initialization."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.schemas.space import SpaceCreate, SpaceUpdate
from app.services.space_service import SpaceService

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_space(
    request: SpaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.SPACE_CREATE)),
) -> dict:
    """Create a new space with workflow from template."""
    service = SpaceService(db)
    try:
        space = await service.create(request, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(space.id),
            "name": space.name,
            "key": space.key,
            "description": space.description,
            "template": space.template,
            "status": space.status,
            "created_at": space.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.get("/")
async def list_spaces(
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """List all active spaces the user has access to."""
    service = SpaceService(db)
    spaces, total = await service.list(page, per_page)

    return {
        "data": [
            {
                "id": str(s.id),
                "name": s.name,
                "key": s.key,
                "description": s.description,
                "template": s.template,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in spaces
        ],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "errors": [],
    }


@router.get("/{key}")
async def get_space(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get space detail by key."""
    service = SpaceService(db)
    space = await service.get_by_key(key.upper())
    if not space:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")

    return {
        "data": {
            "id": str(space.id),
            "name": space.name,
            "key": space.key,
            "description": space.description,
            "template": space.template,
            "management_mode": space.management_mode,
            "settings": space.settings,
            "nav_tabs": space.nav_tabs,
            "status": space.status,
            "created_at": space.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.put("/{key}")
async def update_space(
    key: str,
    request: SpaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.SPACE_EDIT)),
) -> dict:
    """Update space fields (partial update)."""
    service = SpaceService(db)
    try:
        space = await service.update(key.upper(), request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "data": {
            "id": str(space.id),
            "name": space.name,
            "key": space.key,
            "description": space.description,
            "status": space.status,
        },
        "meta": {},
        "errors": [],
    }


@router.delete("/{key}", status_code=status.HTTP_200_OK)
async def archive_space(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.SPACE_DELETE)),
) -> dict:
    """Archive a space (soft delete)."""
    service = SpaceService(db)
    try:
        space = await service.archive(key.upper())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {"data": {"key": space.key, "status": "archived"}, "meta": {}, "errors": []}
