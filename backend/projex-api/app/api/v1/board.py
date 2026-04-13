"""Board API endpoint — returns Kanban board data for a space."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.space import Space
from app.services.workflow_service import WorkflowService
from sqlalchemy import select

router = APIRouter(tags=["board"])


@router.get("/spaces/{space_key}/board")
async def get_board(
    space_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get full Kanban board data: columns, items, swimlanes, quick filters."""
    result = await db.execute(select(Space).where(Space.key == space_key.upper()))
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")

    service = WorkflowService(db)
    board_data = await service.get_board_data(space.id)

    return {"data": board_data, "meta": {}, "errors": []}
