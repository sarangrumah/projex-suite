"""Workflow API endpoints — get and update workflow definitions."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.models.space import Space
from app.models.workflow import Workflow
from app.services.workflow_service import WorkflowService

router = APIRouter(tags=["workflows"])


@router.get("/spaces/{space_key}/workflow")
async def get_workflow(
    space_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get the default workflow with statuses for a space."""
    result = await db.execute(select(Space).where(Space.key == space_key.upper()))
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")

    service = WorkflowService(db)
    workflow = await service.get_workflow_for_space(space.id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No workflow found")

    statuses = await service.get_statuses(workflow.id)

    return {
        "data": {
            "id": str(workflow.id),
            "name": workflow.name,
            "work_item_type": workflow.work_item_type,
            "definition": workflow.definition,
            "statuses": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "category": s.category,
                    "color": s.color,
                    "position": s.position,
                }
                for s in statuses
            ],
        },
        "meta": {},
        "errors": [],
    }


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    """Update workflow definition (transitions). Admin only."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == UUID(workflow_id))
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if "definition" in request:
        workflow.definition = request["definition"]

    if "name" in request:
        workflow.name = request["name"]

    await db.commit()
    await db.refresh(workflow)

    return {
        "data": {
            "id": str(workflow.id),
            "name": workflow.name,
            "definition": workflow.definition,
        },
        "meta": {},
        "errors": [],
    }
