"""Dashboard service — CRUD + widget data aggregation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.dashboard import Dashboard, DashboardWidget
from app.models.goal import Goal
from app.models.space import Space
from app.models.work_item import WorkItem
from app.models.workflow import WorkflowStatus
from app.schemas.dashboard import DashboardCreate, WidgetCreate


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, space_key: str, data: DashboardCreate, user_id: UUID) -> Dashboard:
        space = await self._get_space(space_key)
        dash = Dashboard(space_id=space.id, name=data.name, created_by=user_id)
        self.db.add(dash)
        await self.db.commit()
        await self.db.refresh(dash)
        return dash

    async def get_or_create_default(self, space_key: str, user_id: UUID) -> Dashboard:
        space = await self._get_space(space_key)
        result = await self.db.execute(
            select(Dashboard).where(Dashboard.space_id == space.id, Dashboard.is_default == True)  # noqa: E712
        )
        dash = result.scalar_one_or_none()
        if not dash:
            dash = Dashboard(space_id=space.id, name="Overview", is_default=True, created_by=user_id)
            self.db.add(dash)
            await self.db.flush()
            # Add default widgets
            defaults = [
                ("item_count", "Work Items", "small"),
                ("status_breakdown", "Status Breakdown", "medium"),
                ("priority_chart", "By Priority", "medium"),
                ("goal_progress", "Goals Progress", "medium"),
                ("budget_summary", "Budget", "small"),
            ]
            for i, (wtype, title, size) in enumerate(defaults):
                self.db.add(DashboardWidget(
                    dashboard_id=dash.id, widget_type=wtype, title=title, size=size, position=i,
                ))
            await self.db.commit()
            await self.db.refresh(dash)
        return dash

    async def add_widget(self, dashboard_id: UUID, data: WidgetCreate) -> DashboardWidget:
        count = (await self.db.execute(
            select(func.count()).select_from(DashboardWidget).where(DashboardWidget.dashboard_id == dashboard_id)
        )).scalar() or 0
        widget = DashboardWidget(
            dashboard_id=dashboard_id, widget_type=data.widget_type,
            title=data.title, size=data.size, config=data.config, position=count,
        )
        self.db.add(widget)
        await self.db.commit()
        await self.db.refresh(widget)
        return widget

    async def get_widget_data(self, space_id: UUID, widget_type: str) -> dict:
        """Compute live data for a widget type."""
        if widget_type == "item_count":
            total = (await self.db.execute(
                select(func.count()).select_from(WorkItem).where(WorkItem.space_id == space_id)
            )).scalar() or 0
            return {"total": total}

        elif widget_type == "status_breakdown":
            result = await self.db.execute(
                select(WorkflowStatus.name, func.count(WorkItem.id))
                .join(WorkItem, WorkItem.status_id == WorkflowStatus.id, isouter=True)
                .group_by(WorkflowStatus.name)
            )
            return {"statuses": [{"name": r[0], "count": r[1]} for r in result.fetchall()]}

        elif widget_type == "priority_chart":
            result = await self.db.execute(
                select(WorkItem.priority, func.count())
                .where(WorkItem.space_id == space_id)
                .group_by(WorkItem.priority)
            )
            return {"priorities": [{"name": r[0], "count": r[1]} for r in result.fetchall()]}

        elif widget_type == "goal_progress":
            result = await self.db.execute(
                select(Goal).where(Goal.space_id == space_id).order_by(Goal.created_at.desc()).limit(5)
            )
            goals = result.scalars().all()
            return {"goals": [{"title": g.title, "progress": g.progress, "status": g.status} for g in goals]}

        elif widget_type == "budget_summary":
            result = await self.db.execute(
                select(func.sum(Budget.total_amount), func.sum(Budget.spent_amount))
                .where(Budget.space_id == space_id)
            )
            row = result.fetchone()
            total = row[0] or 0 if row else 0
            spent = row[1] or 0 if row else 0
            return {"total": total, "spent": spent, "remaining": total - spent}

        return {}

    async def _get_space(self, key: str) -> Space:
        result = await self.db.execute(select(Space).where(Space.key == key))
        space = result.scalar_one_or_none()
        if not space:
            raise ValueError(f"Space '{key}' not found")
        return space
