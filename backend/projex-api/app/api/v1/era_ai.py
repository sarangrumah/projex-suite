"""ERA AI chat endpoint — data-driven contextual AI assistant.

Strategy: detect intent → query real DB data → format response → optionally enhance with LLM.
The LLM is supplementary, not primary. Real data always comes first.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.budget import Budget
from app.models.goal import Goal, KeyResult
from app.models.space import Space
from app.models.sprint import Sprint
from app.models.work_item import WorkItem
from app.models.workflow import WorkflowStatus

router = APIRouter(prefix="/ai", tags=["era-ai"])


class ChatRequest(BaseModel):
    model_config = ConfigDict()
    message: str = Field(..., min_length=1, max_length=2000)
    space_key: str | None = None


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Chat with ERA AI — queries real project data first, then optionally enhances with LLM."""
    msg = request.message.lower().strip()
    space = None

    if request.space_key:
        result = await db.execute(select(Space).where(Space.key == request.space_key.upper()))
        space = result.scalar_one_or_none()

    # Auto-detect space if not provided — use the most recent active space
    if not space:
        result = await db.execute(
            select(Space).where(Space.status == "active").order_by(Space.created_at.desc()).limit(1)
        )
        space = result.scalar_one_or_none()

    # Intent detection → data query → formatted response
    reply, suggestions = await _handle_intent(db, msg, request.message, space, current_user)

    return {"data": {"reply": reply, "suggestions": suggestions}, "meta": {}, "errors": []}


@router.get("/suggestions")
async def get_suggestions(
    space_key: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    suggestions = []
    if space_key:
        result = await db.execute(select(Space).where(Space.key == space_key.upper()))
        space = result.scalar_one_or_none()
        if space:
            overdue = (await db.execute(
                select(func.count()).select_from(WorkItem)
                .where(WorkItem.space_id == space.id, WorkItem.due_date < date.today())
            )).scalar() or 0
            if overdue > 0:
                suggestions.append(f"You have {overdue} overdue item(s)")

            unassigned = (await db.execute(
                select(func.count()).select_from(WorkItem)
                .where(WorkItem.space_id == space.id, WorkItem.assignee_id == None)  # noqa: E711
            )).scalar() or 0
            if unassigned > 0:
                suggestions.append(f"{unassigned} item(s) have no assignee")

            goals = (await db.execute(
                select(Goal).where(Goal.space_id == space.id, Goal.status == "behind")
            )).scalars().all()
            if goals:
                suggestions.append(f"{len(goals)} goal(s) are behind schedule")

    if not suggestions:
        suggestions = ["Show project status", "List all items", "Sprint progress"]
    return {"data": {"suggestions": suggestions}, "meta": {}, "errors": []}


async def _handle_intent(db: AsyncSession, msg: str, original: str, space: Space | None, user: dict) -> tuple[str, list[str]]:
    """Detect intent from message and return data-driven response."""

    # ── Search for specific items ───────────────────────────
    if space and _matches(msg, ["find", "search", "show", "list", "cari", "tampilkan", "lihat"]):
        return await _search_items(db, space, original)

    # ── Project status / overview ───────────────────────────
    if _matches(msg, ["status", "overview", "progress", "ringkasan", "terakhir", "update", "how is", "bagaimana"]):
        if space:
            return await _project_status(db, space)
        return ("Please select a space first, or tell me which space you'd like to check.", ["Show spaces"])

    # ── Sprint related ──────────────────────────────────────
    if _matches(msg, ["sprint", "iteration", "backlog"]):
        if space:
            return await _sprint_status(db, space)
        return ("No space selected. Which space's sprint do you want to check?", [])

    # ── Goals / OKR ─────────────────────────────────────────
    if _matches(msg, ["goal", "okr", "objective", "target", "tujuan"]):
        if space:
            return await _goals_status(db, space)
        return ("No space selected.", [])

    # ── Budget ──────────────────────────────────────────────
    if _matches(msg, ["budget", "cost", "spend", "invoice", "biaya", "anggaran"]):
        if space:
            return await _budget_status(db, space)
        return ("No space selected.", [])

    # ── Items by type ───────────────────────────────────────
    if _matches(msg, ["epic", "story", "task", "bug"]):
        if space:
            item_type = next((t for t in ["epic", "story", "task", "bug"] if t in msg), "task")
            return await _items_by_type(db, space, item_type)
        return ("No space selected.", [])

    # ── Help ────────────────────────────────────────────────
    if _matches(msg, ["help", "bantuan", "what can", "apa yang"]):
        return _help_response()

    # ── Default: try to search if space is available ────────
    if space and len(original.strip()) > 2:
        result = await _search_items(db, space, original)
        if "No items found" not in result[0]:
            return result

    # ── Fallback ────────────────────────────────────────────
    return (
        "I can help you with:\n"
        "- **Project status** — ask 'status' or 'progress'\n"
        "- **Find items** — ask 'show drone tasks' or 'find bugs'\n"
        "- **Sprint info** — ask 'sprint progress'\n"
        "- **Goals** — ask 'goal status'\n"
        "- **Budget** — ask 'budget summary'\n\n"
        "Try asking about a specific topic!",
        ["Project status", "List all items", "Sprint progress"],
    )


# ── Data query handlers ─────────────────────────────────────

async def _project_status(db: AsyncSession, space: Space) -> tuple[str, list[str]]:
    """Return real project status with actual item counts per status."""
    # Items by status
    items_result = await db.execute(
        select(WorkflowStatus.name, func.count(WorkItem.id))
        .join(WorkItem, WorkItem.status_id == WorkflowStatus.id, isouter=True)
        .group_by(WorkflowStatus.name, WorkflowStatus.position)
        .order_by(WorkflowStatus.position)
    )
    status_counts = items_result.fetchall()

    total = (await db.execute(
        select(func.count()).select_from(WorkItem).where(WorkItem.space_id == space.id)
    )).scalar() or 0

    # Active sprint
    sprint_result = await db.execute(
        select(Sprint).where(Sprint.space_id == space.id, Sprint.status == "active")
    )
    active_sprint = sprint_result.scalar_one_or_none()

    # Budget
    budget_result = await db.execute(
        select(func.sum(Budget.total_amount), func.sum(Budget.spent_amount))
        .where(Budget.space_id == space.id)
    )
    brow = budget_result.fetchone()

    lines = [f"**{space.name}** ({space.key}) — {space.template} template\n"]
    lines.append(f"**{total} work items:**")
    for name, count in status_counts:
        lines.append(f"  - {name}: {count}")

    if active_sprint:
        lines.append(f"\n**Active Sprint:** {active_sprint.name}")
        sprint_items = (await db.execute(
            select(func.count()).select_from(WorkItem).where(WorkItem.sprint_id == active_sprint.id)
        )).scalar() or 0
        lines.append(f"  Items in sprint: {sprint_items}")

    if brow and brow[0]:
        pct = round((brow[1] or 0) / brow[0] * 100) if brow[0] > 0 else 0
        lines.append(f"\n**Budget:** Rp{brow[1] or 0:,.0f} / Rp{brow[0]:,.0f} ({pct}% used)")

    return ("\n".join(lines), ["Show all items", "Sprint details", "Goal status"])


async def _search_items(db: AsyncSession, space: Space, query: str) -> tuple[str, list[str]]:
    """Search items in the space by keyword."""
    # Extract search terms (remove common words)
    skip_words = {"show", "find", "search", "list", "all", "my", "the", "in", "for", "me",
                  "cari", "tampilkan", "lihat", "semua", "items", "item", "tasks", "task"}
    words = [w for w in query.split() if w.lower() not in skip_words and len(w) > 1]
    search_term = " ".join(words) if words else query

    pattern = f"%{search_term}%"
    result = await db.execute(
        select(WorkItem)
        .where(WorkItem.space_id == space.id, or_(
            WorkItem.title.ilike(pattern),
            WorkItem.key.ilike(pattern),
            WorkItem.type.ilike(pattern),
        ))
        .order_by(WorkItem.created_at.desc())
        .limit(10)
    )
    items = list(result.scalars().all())

    if not items:
        return (f"No items found matching '{search_term}' in {space.key}.", ["Show all items", "Project status"])

    # Get status names
    status_names = {}
    if items:
        status_ids = [i.status_id for i in items if i.status_id]
        if status_ids:
            st_result = await db.execute(select(WorkflowStatus).where(WorkflowStatus.id.in_(status_ids)))
            status_names = {s.id: s.name for s in st_result.scalars().all()}

    lines = [f"**Found {len(items)} item(s) matching '{search_term}':**\n"]
    for item in items:
        status = status_names.get(item.status_id, "—")
        lines.append(f"- **{item.key}** [{item.type}] {item.title}")
        lines.append(f"  Status: {status} | Priority: {item.priority}")

    return ("\n".join(lines), ["Project status", "Show bugs", "Show epics"])


async def _sprint_status(db: AsyncSession, space: Space) -> tuple[str, list[str]]:
    """Return sprint info with item counts."""
    result = await db.execute(
        select(Sprint).where(Sprint.space_id == space.id).order_by(Sprint.created_at.desc()).limit(5)
    )
    sprints = list(result.scalars().all())

    if not sprints:
        return (f"No sprints in {space.key} yet.", ["Create a sprint"])

    lines = [f"**Sprints in {space.key}:**\n"]
    for s in sprints:
        item_count = (await db.execute(
            select(func.count()).select_from(WorkItem).where(WorkItem.sprint_id == s.id)
        )).scalar() or 0
        dates = ""
        if s.start_date:
            dates = f" ({s.start_date}"
            if s.end_date:
                dates += f" → {s.end_date}"
            dates += ")"
        lines.append(f"- **{s.name}** [{s.status}] — {item_count} items{dates}")
        if s.goal:
            lines.append(f"  Goal: {s.goal}")

    # Backlog count
    backlog = (await db.execute(
        select(func.count()).select_from(WorkItem)
        .where(WorkItem.space_id == space.id, WorkItem.sprint_id == None)  # noqa: E711
    )).scalar() or 0
    lines.append(f"\n**Backlog:** {backlog} items not in any sprint")

    return ("\n".join(lines), ["Project status", "Show backlog items"])


async def _goals_status(db: AsyncSession, space: Space) -> tuple[str, list[str]]:
    """Return goals with key results progress."""
    result = await db.execute(
        select(Goal).where(Goal.space_id == space.id).order_by(Goal.created_at.desc())
    )
    goals = list(result.scalars().all())

    if not goals:
        return (f"No goals in {space.key} yet.", ["Create a goal"])

    lines = [f"**Goals in {space.key}:**\n"]
    for g in goals:
        lines.append(f"- **{g.title}** [{g.status}] — {g.progress}% complete")

        kr_result = await db.execute(
            select(KeyResult).where(KeyResult.goal_id == g.id).order_by(KeyResult.position)
        )
        for kr in kr_result.scalars().all():
            lines.append(f"  - {kr.title}: {kr.current_value}/{kr.target_value} {kr.unit or ''}")

    return ("\n".join(lines), ["Project status", "Sprint progress"])


async def _budget_status(db: AsyncSession, space: Space) -> tuple[str, list[str]]:
    """Return budget summary with line items."""
    result = await db.execute(
        select(Budget).where(Budget.space_id == space.id).order_by(Budget.created_at.desc())
    )
    budgets = list(result.scalars().all())

    if not budgets:
        return (f"No budgets in {space.key} yet.", ["Create a budget"])

    lines = [f"**Budgets in {space.key}:**\n"]
    for b in budgets:
        remaining = b.total_amount - b.spent_amount
        pct = round((b.spent_amount / b.total_amount) * 100) if b.total_amount > 0 else 0
        lines.append(f"- **{b.name}** [{b.status}]")
        lines.append(f"  Total: Rp{b.total_amount:,.0f} | Spent: Rp{b.spent_amount:,.0f} ({pct}%) | Remaining: Rp{remaining:,.0f}")

    return ("\n".join(lines), ["Project status", "Generate invoice"])


async def _items_by_type(db: AsyncSession, space: Space, item_type: str) -> tuple[str, list[str]]:
    """List items filtered by type."""
    result = await db.execute(
        select(WorkItem).where(WorkItem.space_id == space.id, WorkItem.type == item_type)
        .order_by(WorkItem.created_at.desc()).limit(15)
    )
    items = list(result.scalars().all())

    if not items:
        return (f"No {item_type}s in {space.key}.", ["Show all items"])

    lines = [f"**{item_type.title()}s in {space.key} ({len(items)}):**\n"]
    for item in items:
        lines.append(f"- **{item.key}** {item.title} [{item.priority}]")

    return ("\n".join(lines), ["Project status", "Show all items"])


def _help_response() -> tuple[str, list[str]]:
    return (
        "**Hi! I'm ERA, your project assistant.**\n\n"
        "I can help you with:\n"
        "- **'status'** or **'progress'** — project overview with real data\n"
        "- **'show drone'** or **'find bugs'** — search work items\n"
        "- **'sprint'** — sprint progress and backlog\n"
        "- **'goals'** — OKR tracking with key results\n"
        "- **'budget'** — budget summary and utilization\n"
        "- **'epics'** / **'tasks'** / **'bugs'** — filter by type\n\n"
        "All responses use your **real project data**, not generated text!",
        ["Project status", "Show all items", "Sprint progress"],
    )


def _matches(msg: str, keywords: list[str]) -> bool:
    return any(kw in msg for kw in keywords)
