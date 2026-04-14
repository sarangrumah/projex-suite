"""Dashboard API endpoints."""

from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.models.dashboard import DashboardWidget
from app.models.space import Space
from app.schemas.dashboard import WidgetCreate
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboards"])


@router.get("/spaces/{space_key}/dashboard")
async def get_dashboard(
    space_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get the default dashboard with live widget data."""
    service = DashboardService(db)
    try:
        dash = await service.get_or_create_default(space_key.upper(), UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Get space_id and widgets explicitly (avoid lazy load)
    result = await db.execute(select(Space).where(Space.key == space_key.upper()))
    space = result.scalar_one_or_none()

    widgets_result = await db.execute(
        select(DashboardWidget)
        .where(DashboardWidget.dashboard_id == dash.id)
        .order_by(DashboardWidget.position)
    )
    widgets = list(widgets_result.scalars().all())

    widgets_data = []
    for w in widgets:
        data = await service.get_widget_data(space.id, w.widget_type) if space else {}
        widgets_data.append({
            "id": str(w.id), "widget_type": w.widget_type, "title": w.title,
            "size": w.size, "position": w.position, "config": w.config, "data": data,
        })

    return {
        "data": {
            "id": str(dash.id), "name": dash.name,
            "widgets": widgets_data,
        },
        "meta": {},
        "errors": [],
    }


@router.post("/dashboards/{dashboard_id}/widgets", status_code=201)
async def add_widget(
    dashboard_id: str, request: WidgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = DashboardService(db)
    w = await service.add_widget(UUID(dashboard_id), request)
    return {
        "data": {"id": str(w.id), "widget_type": w.widget_type, "title": w.title, "size": w.size},
        "meta": {}, "errors": [],
    }
