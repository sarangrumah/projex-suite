"""Space service — business logic for space CRUD + template initialization."""

import re
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.space import Space
from app.models.workflow import Workflow, WorkflowStatus
from app.schemas.space import SpaceCreate, SpaceUpdate

# ── Template definitions ────────────────────────────────────
_TEMPLATES = {
    "scrum": {
        "statuses": [
            {"name": "To Do", "category": "todo", "color": "#6B7280", "position": 0},
            {"name": "In Progress", "category": "in_progress", "color": "#3B82F6", "position": 1},
            {"name": "In Review", "category": "in_progress", "color": "#F59E0B", "position": 2},
            {"name": "Done", "category": "done", "color": "#059669", "position": 3},
        ],
        "item_types": ["epic", "story", "task", "bug"],
        "nav_tabs": ["board", "backlog", "sprints", "timeline", "wiki"],
    },
    "kanban": {
        "statuses": [
            {"name": "Backlog", "category": "todo", "color": "#9CA3AF", "position": 0},
            {"name": "To Do", "category": "todo", "color": "#6B7280", "position": 1},
            {"name": "In Progress", "category": "in_progress", "color": "#3B82F6", "position": 2},
            {"name": "Done", "category": "done", "color": "#059669", "position": 3},
        ],
        "item_types": ["task", "bug"],
        "nav_tabs": ["board", "list", "wiki"],
    },
    "bug": {
        "statuses": [
            {"name": "Open", "category": "todo", "color": "#DC2626", "position": 0},
            {"name": "Investigating", "category": "in_progress", "color": "#F59E0B", "position": 1},
            {"name": "Fixing", "category": "in_progress", "color": "#3B82F6", "position": 2},
            {"name": "Resolved", "category": "done", "color": "#059669", "position": 3},
            {"name": "Closed", "category": "done", "color": "#6B7280", "position": 4},
        ],
        "item_types": ["bug", "task"],
        "nav_tabs": ["board", "list"],
    },
    "blank": {
        "statuses": [
            {"name": "To Do", "category": "todo", "color": "#6B7280", "position": 0},
            {"name": "In Progress", "category": "in_progress", "color": "#3B82F6", "position": 1},
            {"name": "Done", "category": "done", "color": "#059669", "position": 2},
        ],
        "item_types": ["task"],
        "nav_tabs": ["board", "list"],
    },
}


class SpaceService:
    """Space CRUD with template-based initialization."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: SpaceCreate, user_id: UUID) -> Space:
        """Create a space with workflow from template."""
        key = data.key or self._generate_key(data.name)

        # Check unique key
        existing = await self.db.execute(select(Space).where(Space.key == key))
        if existing.scalar_one_or_none():
            raise ValueError(f"Space key '{key}' already exists")

        template_def = _TEMPLATES.get(data.template, _TEMPLATES["blank"])

        space = Space(
            name=data.name,
            key=key,
            description=data.description,
            template=data.template,
            management_mode=data.management_mode,
            nav_tabs=template_def["nav_tabs"],
            created_by=user_id,
        )
        self.db.add(space)
        await self.db.flush()  # Get space.id

        # Create default workflow
        await self._create_workflow(space, template_def)
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def list(self, page: int = 1, per_page: int = 50) -> tuple[list[Space], int]:
        """List active spaces with pagination."""
        offset = (page - 1) * per_page
        query = (
            select(Space)
            .where(Space.status == "active")
            .order_by(Space.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_q = select(func.count()).select_from(Space).where(Space.status == "active")
        total = (await self.db.execute(count_q)).scalar() or 0
        return items, total

    async def get_by_key(self, key: str) -> Space | None:
        """Get a single space by its key."""
        result = await self.db.execute(select(Space).where(Space.key == key))
        return result.scalar_one_or_none()

    async def update(self, key: str, data: SpaceUpdate) -> Space:
        """Update space fields (partial update)."""
        space = await self.get_by_key(key)
        if not space:
            raise ValueError(f"Space '{key}' not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(space, field, value)

        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def archive(self, key: str) -> Space:
        """Soft-delete a space by setting status to 'archived'."""
        space = await self.get_by_key(key)
        if not space:
            raise ValueError(f"Space '{key}' not found")

        space.status = "archived"
        await self.db.commit()
        await self.db.refresh(space)
        return space

    # ── Private helpers ─────────────────────────────────────

    def _generate_key(self, name: str) -> str:
        """Auto-generate a key from space name (e.g. 'PT AIM' → 'AIM')."""
        # Take uppercase letters/digits, skip common prefixes
        words = name.upper().split()
        if len(words) == 1:
            key = re.sub(r"[^A-Z0-9]", "", words[0])[:10]
        else:
            # Take first letter of each word
            key = "".join(w[0] for w in words if w[0].isalpha())[:10]

        return key or "PROJ"

    async def _create_workflow(self, space: Space, template_def: dict) -> None:
        """Create the default workflow + statuses for a space."""
        workflow = Workflow(
            space_id=space.id,
            name=f"{space.name} Workflow",
            work_item_type="all",
            is_default=True,
            definition=self._build_transitions(template_def["statuses"]),
        )
        self.db.add(workflow)
        await self.db.flush()

        for status_def in template_def["statuses"]:
            status = WorkflowStatus(
                workflow_id=workflow.id,
                name=status_def["name"],
                category=status_def["category"],
                color=status_def["color"],
                position=status_def["position"],
            )
            self.db.add(status)

    def _build_transitions(self, statuses: list[dict]) -> dict:
        """Build linear transitions between statuses."""
        transitions = []
        for i in range(len(statuses) - 1):
            transitions.append({
                "from": statuses[i]["name"],
                "to": statuses[i + 1]["name"],
                "conditions": [],
            })
            # Also allow moving backward
            transitions.append({
                "from": statuses[i + 1]["name"],
                "to": statuses[i]["name"],
                "conditions": [],
            })
        return {"transitions": transitions}
