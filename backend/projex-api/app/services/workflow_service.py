"""Workflow service — transition validation, status management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowStatus


class WorkflowService:
    """Handles workflow transitions and board data assembly."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_workflow_for_space(self, space_id: UUID) -> Workflow | None:
        """Get the default workflow for a space."""
        result = await self.db.execute(
            select(Workflow).where(
                Workflow.space_id == space_id, Workflow.is_default == True  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_statuses(self, workflow_id: UUID) -> list[WorkflowStatus]:
        """Get all statuses for a workflow, ordered by position."""
        result = await self.db.execute(
            select(WorkflowStatus)
            .where(WorkflowStatus.workflow_id == workflow_id)
            .order_by(WorkflowStatus.position)
        )
        return list(result.scalars().all())

    async def validate_transition(
        self, workflow: Workflow, from_status_id: UUID | None, to_status_id: UUID
    ) -> bool:
        """Check if a transition from one status to another is allowed."""
        if from_status_id is None:
            return True  # Initial assignment is always valid

        # Get status names for lookup
        statuses = await self.get_statuses(workflow.id)
        status_map = {s.id: s.name for s in statuses}

        from_name = status_map.get(from_status_id)
        to_name = status_map.get(to_status_id)

        if not from_name or not to_name:
            return False

        # Check transitions in workflow definition
        transitions = workflow.definition.get("transitions", [])
        for t in transitions:
            if t["from"] == from_name and t["to"] == to_name:
                return True

        return False

    async def get_board_data(self, space_id: UUID) -> dict:
        """Assemble board data: columns with items grouped by status."""
        from app.models.work_item import WorkItem

        workflow = await self.get_workflow_for_space(space_id)
        if not workflow:
            return {"columns": [], "swimlanes": {"type": "none", "groups": []}}

        statuses = await self.get_statuses(workflow.id)

        # Fetch all items for this space
        result = await self.db.execute(
            select(WorkItem)
            .where(WorkItem.space_id == space_id)
            .order_by(WorkItem.position, WorkItem.created_at)
        )
        all_items = list(result.scalars().all())

        # Group items by status
        items_by_status: dict[UUID, list] = {s.id: [] for s in statuses}
        for item in all_items:
            if item.status_id in items_by_status:
                items_by_status[item.status_id].append(item)

        columns = []
        for status in statuses:
            status_items = items_by_status.get(status.id, [])
            columns.append({
                "status": {
                    "id": str(status.id),
                    "name": status.name,
                    "category": status.category,
                    "color": status.color,
                    "position": status.position,
                },
                "items": [
                    {
                        "id": str(i.id),
                        "key": i.key,
                        "title": i.title,
                        "type": i.type,
                        "priority": i.priority,
                        "assignee_id": str(i.assignee_id) if i.assignee_id else None,
                        "estimate_points": i.estimate_points,
                        "labels": i.labels or [],
                        "position": i.position,
                    }
                    for i in status_items
                ],
                "count": len(status_items),
            })

        # Collect quick filter options
        all_assignees = list({str(i.assignee_id) for i in all_items if i.assignee_id})
        all_types = list({i.type for i in all_items})
        all_labels = list({l for i in all_items for l in (i.labels or [])})

        return {
            "columns": columns,
            "swimlanes": {"type": "none", "groups": []},
            "quick_filters": {
                "assignees": all_assignees,
                "types": all_types,
                "labels": all_labels,
            },
        }
