"""Custom Field API endpoints: CRUD per space."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate
from app.services.custom_field_service import CustomFieldService

router = APIRouter(tags=["custom-fields"])


@router.post("/spaces/{space_key}/fields", status_code=status.HTTP_201_CREATED)
async def create_field(
    space_key: str,
    request: CustomFieldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    """Create a custom field definition for a space. Admin only."""
    service = CustomFieldService(db)
    try:
        field = await service.create(space_key.upper(), request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(field.id),
            "name": field.name,
            "field_type": field.field_type,
            "is_required": field.is_required,
            "position": field.position,
            "config": field.config,
            "created_at": field.created_at.isoformat(),
        },
        "meta": {},
        "errors": [],
    }


@router.get("/spaces/{space_key}/fields")
async def list_fields(
    space_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """List all custom field definitions for a space."""
    service = CustomFieldService(db)
    try:
        fields = await service.list(space_key.upper())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "data": [
            {
                "id": str(f.id),
                "name": f.name,
                "field_type": f.field_type,
                "description": f.description,
                "is_required": f.is_required,
                "position": f.position,
                "config": f.config,
            }
            for f in fields
        ],
        "meta": {},
        "errors": [],
    }


@router.put("/fields/{field_id}")
async def update_field(
    field_id: str,
    request: CustomFieldUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    """Update a custom field definition. Admin only."""
    service = CustomFieldService(db)
    try:
        field = await service.update(UUID(field_id), request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "id": str(field.id),
            "name": field.name,
            "field_type": field.field_type,
            "config": field.config,
            "position": field.position,
        },
        "meta": {},
        "errors": [],
    }


@router.delete("/fields/{field_id}")
async def delete_field(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    """Delete a custom field definition. Admin only."""
    service = CustomFieldService(db)
    try:
        await service.delete(UUID(field_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {"data": {"deleted": True}, "meta": {}, "errors": []}
