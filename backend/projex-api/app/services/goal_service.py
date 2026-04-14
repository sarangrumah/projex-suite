"""Goal service — OKR CRUD with auto-progress calculation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, KeyResult
from app.models.space import Space
from app.schemas.goal import GoalCreate, GoalUpdate, KeyResultCreate, KeyResultUpdate


class GoalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_goal(self, space_key: str, data: GoalCreate, user_id: UUID) -> Goal:
        space = await self._get_space(space_key)
        goal = Goal(
            space_id=space.id, title=data.title, description=data.description,
            start_date=data.start_date, due_date=data.due_date, owner_id=user_id,
        )
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def list_goals(self, space_key: str) -> list[Goal]:
        space = await self._get_space(space_key)
        result = await self.db.execute(
            select(Goal).where(Goal.space_id == space.id).order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_goal(self, goal_id: UUID) -> Goal | None:
        result = await self.db.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()

    async def update_goal(self, goal_id: UUID, data: GoalUpdate) -> Goal:
        goal = await self.get_goal(goal_id)
        if not goal:
            raise ValueError("Goal not found")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(goal, k, v)
        goal.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def delete_goal(self, goal_id: UUID) -> None:
        goal = await self.get_goal(goal_id)
        if not goal:
            raise ValueError("Goal not found")
        # Delete key results first
        krs = await self.db.execute(select(KeyResult).where(KeyResult.goal_id == goal_id))
        for kr in krs.scalars().all():
            await self.db.delete(kr)
        await self.db.delete(goal)
        await self.db.commit()

    # ── Key Results ─────────────────────────────────────────

    async def add_key_result(self, goal_id: UUID, data: KeyResultCreate) -> KeyResult:
        goal = await self.get_goal(goal_id)
        if not goal:
            raise ValueError("Goal not found")
        count = (await self.db.execute(
            select(func.count()).select_from(KeyResult).where(KeyResult.goal_id == goal_id)
        )).scalar() or 0

        kr = KeyResult(
            goal_id=goal_id, title=data.title, metric_type=data.metric_type,
            target_value=data.target_value, start_value=data.start_value,
            unit=data.unit, position=count,
        )
        self.db.add(kr)
        await self.db.commit()
        await self.db.refresh(kr)
        return kr

    async def update_key_result(self, kr_id: UUID, data: KeyResultUpdate) -> KeyResult:
        result = await self.db.execute(select(KeyResult).where(KeyResult.id == kr_id))
        kr = result.scalar_one_or_none()
        if not kr:
            raise ValueError("Key result not found")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(kr, k, v)
        await self.db.commit()
        await self.db.refresh(kr)

        # Recalculate goal progress
        await self._recalculate_progress(kr.goal_id)
        return kr

    async def list_key_results(self, goal_id: UUID) -> list[KeyResult]:
        result = await self.db.execute(
            select(KeyResult).where(KeyResult.goal_id == goal_id).order_by(KeyResult.position)
        )
        return list(result.scalars().all())

    async def _recalculate_progress(self, goal_id: UUID) -> None:
        """Recalculate goal progress from key results."""
        krs = await self.list_key_results(goal_id)
        if not krs:
            return
        total_progress = 0.0
        for kr in krs:
            rng = kr.target_value - kr.start_value
            if rng > 0:
                total_progress += min(((kr.current_value - kr.start_value) / rng) * 100, 100)
        avg = total_progress / len(krs)

        goal = await self.get_goal(goal_id)
        if goal:
            goal.progress = round(avg, 1)
            if avg >= 100:
                goal.status = "completed"
            goal.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def _get_space(self, key: str) -> Space:
        result = await self.db.execute(select(Space).where(Space.key == key))
        space = result.scalar_one_or_none()
        if not space:
            raise ValueError(f"Space '{key}' not found")
        return space
