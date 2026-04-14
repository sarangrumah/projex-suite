"""Item service — business logic for work items, comments, worklogs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.space import Space
from app.models.work_item import WorkItem
from app.models.worklog import Worklog
from app.schemas.item import CommentCreate, ItemCreate, ItemUpdate, WorklogCreate


class ItemService:
    """Work item CRUD with key generation and workflow validation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Create ──────────────────────────────────────────────

    async def create(self, space_key: str, data: ItemCreate, user_id: UUID) -> WorkItem:
        """Create a work item with auto-generated key (e.g. AIM-1)."""
        space = await self._get_space(space_key)

        # Validate parent (no circular refs)
        if data.parent_id:
            await self._validate_parent(data.parent_id, None)

        # Generate key: increment space sequence
        space.item_sequence += 1
        seq = space.item_sequence
        key = f"{space.key}-{seq}"

        # Get initial status (first status in default workflow)
        status_id = await self._get_initial_status(space.id)

        item = WorkItem(
            space_id=space.id,
            key=key,
            sequence_num=seq,
            type=data.type,
            title=data.title,
            description=data.description,
            status_id=status_id,
            priority=data.priority,
            assignee_id=data.assignee_id,
            reporter_id=user_id,
            parent_id=data.parent_id,
            sprint_id=data.sprint_id,
            due_date=data.due_date,
            start_date=data.start_date,
            estimate_points=data.estimate_points,
            estimate_hours=data.estimate_hours,
            labels=data.labels,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ── List ────────────────────────────────────────────────

    async def list(
        self, space_key: str, page: int = 1, per_page: int = 50
    ) -> tuple[list[WorkItem], int]:
        """List work items for a space with pagination."""
        space = await self._get_space(space_key)
        offset = (page - 1) * per_page

        query = (
            select(WorkItem)
            .where(WorkItem.space_id == space.id)
            .order_by(WorkItem.position, WorkItem.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_q = (
            select(func.count()).select_from(WorkItem).where(WorkItem.space_id == space.id)
        )
        total = (await self.db.execute(count_q)).scalar() or 0
        return items, total

    # ── Get ──────────────────────────────────────────────────

    async def get_by_key(self, item_key: str) -> WorkItem | None:
        """Get a work item by its key (e.g. AIM-101)."""
        result = await self.db.execute(select(WorkItem).where(WorkItem.key == item_key))
        return result.scalar_one_or_none()

    # ── Update ──────────────────────────────────────────────

    async def update(self, item_key: str, data: ItemUpdate) -> WorkItem:
        """Partial update of a work item."""
        item = await self.get_by_key(item_key)
        if not item:
            raise ValueError(f"Work item '{item_key}' not found")

        if data.parent_id:
            await self._validate_parent(data.parent_id, item.id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        item.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ── Delete (soft) ───────────────────────────────────────

    async def delete(self, item_key: str) -> None:
        """Soft delete — remove from board but keep in DB."""
        item = await self.get_by_key(item_key)
        if not item:
            raise ValueError(f"Work item '{item_key}' not found")

        await self.db.delete(item)
        await self.db.commit()

    # ── Move (status transition) ────────────────────────────

    async def move(self, item_key: str, status_id: UUID, position: int = 0) -> WorkItem:
        """Move item to new status (board drag-drop)."""
        item = await self.get_by_key(item_key)
        if not item:
            raise ValueError(f"Work item '{item_key}' not found")

        item.status_id = status_id
        item.position = position
        item.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ── Comments ────────────────────────────────────────────

    async def add_comment(
        self, item_key: str, data: CommentCreate, user_id: UUID
    ) -> Comment:
        """Add a comment to a work item."""
        item = await self.get_by_key(item_key)
        if not item:
            raise ValueError(f"Work item '{item_key}' not found")

        comment = Comment(
            work_item_id=item.id,
            author_id=user_id,
            parent_id=data.parent_id,
            body=data.body,
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def list_comments(self, item_key: str) -> list[Comment]:
        """List all comments for a work item."""
        item = await self.get_by_key(item_key)
        if not item:
            raise ValueError(f"Work item '{item_key}' not found")

        result = await self.db.execute(
            select(Comment)
            .where(Comment.work_item_id == item.id)
            .order_by(Comment.created_at)
        )
        return list(result.scalars().all())

    # ── Worklogs ────────────────────────────────────────────

    async def add_worklog(
        self, item_key: str, data: WorklogCreate, user_id: UUID
    ) -> Worklog:
        """Log time against a work item."""
        item = await self.get_by_key(item_key)
        if not item:
            raise ValueError(f"Work item '{item_key}' not found")

        worklog = Worklog(
            work_item_id=item.id,
            user_id=user_id,
            time_spent_seconds=data.time_spent_seconds,
            description=data.description,
            log_date=data.log_date,
        )
        self.db.add(worklog)

        # Update total time on item
        item.time_spent_seconds += data.time_spent_seconds
        item.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(worklog)
        return worklog

    # ── Private helpers ─────────────────────────────────────

    async def _get_space(self, key: str) -> Space:
        result = await self.db.execute(select(Space).where(Space.key == key))
        space = result.scalar_one_or_none()
        if not space:
            raise ValueError(f"Space '{key}' not found")
        return space

    async def _get_initial_status(self, space_id: UUID) -> UUID | None:
        """Get the first status of the default workflow for a space."""
        from app.models.workflow import Workflow, WorkflowStatus

        wf = await self.db.execute(
            select(Workflow).where(
                Workflow.space_id == space_id, Workflow.is_default == True  # noqa: E712
            )
        )
        workflow = wf.scalar_one_or_none()
        if not workflow:
            return None

        st = await self.db.execute(
            select(WorkflowStatus)
            .where(WorkflowStatus.workflow_id == workflow.id)
            .order_by(WorkflowStatus.position)
            .limit(1)
        )
        status = st.scalar_one_or_none()
        return status.id if status else None

    async def _validate_parent(self, parent_id: UUID, item_id: UUID | None) -> None:
        """Ensure no circular parent-child reference."""
        if item_id and parent_id == item_id:
            raise ValueError("An item cannot be its own parent")

        parent = await self.db.execute(
            select(WorkItem).where(WorkItem.id == parent_id)
        )
        if not parent.scalar_one_or_none():
            raise ValueError("Parent item not found")
