"""Work Item API endpoints: CRUD + comments + worklogs."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.schemas.item import (
    CommentCreate,
    ItemCreate,
    ItemMoveRequest,
    ItemUpdate,
    WorklogCreate,
)
from app.services.item_service import ItemService

router = APIRouter(tags=["items"])


# ── Work Items CRUD ─────────────────────────────────────────

@router.post("/spaces/{space_key}/items", status_code=status.HTTP_201_CREATED)
async def create_item(
    space_key: str,
    request: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ITEM_CREATE)),
) -> dict:
    """Create a work item in the given space."""
    service = ItemService(db)
    try:
        item = await service.create(space_key.upper(), request, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(item.id),
            "key": item.key,
            "type": item.type,
            "title": item.title,
            "status_id": str(item.status_id) if item.status_id else None,
            "priority": item.priority,
            "assignee_id": str(item.assignee_id) if item.assignee_id else None,
            "parent_id": str(item.parent_id) if item.parent_id else None,
            "created_at": item.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.get("/spaces/{space_key}/items")
async def list_items(
    space_key: str,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """List work items in a space with pagination."""
    service = ItemService(db)
    try:
        items, total = await service.list(space_key.upper(), page, per_page)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "data": [
            {
                "id": str(i.id),
                "key": i.key,
                "type": i.type,
                "title": i.title,
                "status_id": str(i.status_id) if i.status_id else None,
                "priority": i.priority,
                "assignee_id": str(i.assignee_id) if i.assignee_id else None,
                "position": i.position,
            }
            for i in items
        ],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "errors": [],
    }


@router.get("/items/{item_key}")
async def get_item(
    item_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get work item detail by key."""
    service = ItemService(db)
    item = await service.get_by_key(item_key.upper())
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return {
        "data": {
            "id": str(item.id),
            "key": item.key,
            "type": item.type,
            "title": item.title,
            "description": item.description,
            "status_id": str(item.status_id) if item.status_id else None,
            "priority": item.priority,
            "assignee_id": str(item.assignee_id) if item.assignee_id else None,
            "reporter_id": str(item.reporter_id) if item.reporter_id else None,
            "parent_id": str(item.parent_id) if item.parent_id else None,
            "sprint_id": str(item.sprint_id) if item.sprint_id else None,
            "due_date": item.due_date.isoformat() if item.due_date else None,
            "start_date": item.start_date.isoformat() if item.start_date else None,
            "estimate_points": item.estimate_points,
            "estimate_hours": item.estimate_hours,
            "time_spent_seconds": item.time_spent_seconds,
            "labels": item.labels,
            "custom_fields": item.custom_fields,
            "position": item.position,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.put("/items/{item_key}")
async def update_item(
    item_key: str,
    request: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ITEM_EDIT)),
) -> dict:
    """Partial update of a work item."""
    service = ItemService(db)
    try:
        item = await service.update(item_key.upper(), request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(item.id),
            "key": item.key,
            "title": item.title,
            "status_id": str(item.status_id) if item.status_id else None,
            "priority": item.priority,
            "updated_at": item.updated_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.delete("/items/{item_key}")
async def delete_item(
    item_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ITEM_DELETE)),
) -> dict:
    """Soft delete a work item."""
    service = ItemService(db)
    try:
        await service.delete(item_key.upper())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {"data": {"key": item_key.upper(), "deleted": True}, "meta": {}, "errors": []}


@router.put("/items/{item_key}/move")
async def move_item(
    item_key: str,
    request: ItemMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ITEM_TRANSITION)),
) -> dict:
    """Move item to a new status (board drag-drop)."""
    service = ItemService(db)
    try:
        item = await service.move(item_key.upper(), request.status_id, request.position)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "key": item.key,
            "status_id": str(item.status_id),
            "position": item.position,
        },
        "meta": {},
        "errors": [],
    }


# ── Comments ────────────────────────────────────────────────

@router.post("/items/{item_key}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(
    item_key: str,
    request: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ITEM_COMMENT)),
) -> dict:
    """Add a comment to a work item."""
    service = ItemService(db)
    try:
        comment = await service.add_comment(
            item_key.upper(), request, UUID(current_user["sub"])
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(comment.id),
            "work_item_id": str(comment.work_item_id),
            "author_id": str(comment.author_id),
            "body": comment.body,
            "created_at": comment.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.get("/items/{item_key}/comments")
async def list_comments(
    item_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """List all comments for a work item."""
    service = ItemService(db)
    try:
        comments = await service.list_comments(item_key.upper())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "data": [
            {
                "id": str(c.id),
                "author_id": str(c.author_id),
                "parent_id": str(c.parent_id) if c.parent_id else None,
                "body": c.body,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ],
        "meta": {},
        "errors": [],
    }


# ── Worklogs ────────────────────────────────────────────────

@router.post("/items/{item_key}/worklogs", status_code=status.HTTP_201_CREATED)
async def add_worklog(
    item_key: str,
    request: WorklogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.TIMESHEET_LOG)),
) -> dict:
    """Log work time against a work item."""
    service = ItemService(db)
    try:
        worklog = await service.add_worklog(
            item_key.upper(), request, UUID(current_user["sub"])
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(worklog.id),
            "work_item_id": str(worklog.work_item_id),
            "time_spent_seconds": worklog.time_spent_seconds,
            "description": worklog.description,
            "log_date": worklog.log_date.isoformat(),
            "created_at": worklog.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }
