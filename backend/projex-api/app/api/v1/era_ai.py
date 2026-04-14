"""ERA AI chat endpoint — contextual AI assistant."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.space import Space
from app.models.work_item import WorkItem
from app.models.sprint import Sprint
from app.models.goal import Goal
from app.models.budget import Budget
from app.services.ai_provider import get_ai_provider

router = APIRouter(prefix="/ai", tags=["era-ai"])


class ChatRequest(BaseModel):
    model_config = ConfigDict()
    message: str = Field(..., min_length=1, max_length=2000)
    space_key: str | None = None  # Optional context


class ChatResponse(BaseModel):
    reply: str
    suggestions: list[str] = []


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Chat with ERA AI — context-aware project assistant."""
    ai = get_ai_provider()

    # Build context from current space
    context = await _build_context(db, request.space_key, current_user)

    # Build prompt
    system_prompt = f"""You are ERA, an AI project management assistant for ProjeX Suite.
You help users manage their software projects. Be concise, friendly, and actionable.

Current user: {current_user.get('role', 'member')}

{context}

When suggesting actions, use specific item keys (like AIM-1) and concrete next steps.
If the user asks to do something you can't do directly, tell them which page or API to use."""

    # Call AI
    try:
        import httpx

        provider = get_ai_provider()
        if hasattr(provider, 'api_key') and provider.api_key:
            # Claude
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": provider.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": provider.model,
                        "max_tokens": 1024,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": request.message}],
                    },
                )
                response.raise_for_status()
                reply = response.json()["content"][0]["text"]
        else:
            # Ollama
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{provider.base_url}/api/generate",
                    json={
                        "model": provider.model,
                        "prompt": f"{system_prompt}\n\nUser: {request.message}\n\nERA:",
                        "stream": False,
                    },
                )
                response.raise_for_status()
                reply = response.json().get("response", "I'm having trouble connecting. Please try again.")
    except Exception as e:
        reply = f"I'm currently offline (AI service unavailable). You can still use all ProjeX features directly. Error: {type(e).__name__}"

    # Generate suggestions based on context
    suggestions = _generate_suggestions(request.message)

    return {
        "data": {"reply": reply, "suggestions": suggestions},
        "meta": {},
        "errors": [],
    }


@router.get("/suggestions")
async def get_suggestions(
    space_key: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get proactive suggestions based on current space state."""
    suggestions = []

    if space_key:
        result = await db.execute(select(Space).where(Space.key == space_key.upper()))
        space = result.scalar_one_or_none()
        if space:
            # Check overdue items
            from datetime import date
            overdue = (await db.execute(
                select(func.count()).select_from(WorkItem)
                .where(WorkItem.space_id == space.id, WorkItem.due_date < date.today())
            )).scalar() or 0
            if overdue > 0:
                suggestions.append(f"You have {overdue} overdue item(s). Want me to list them?")

            # Check items without assignee
            unassigned = (await db.execute(
                select(func.count()).select_from(WorkItem)
                .where(WorkItem.space_id == space.id, WorkItem.assignee_id == None)  # noqa: E711
            )).scalar() or 0
            if unassigned > 0:
                suggestions.append(f"{unassigned} item(s) have no assignee.")

            # Check goals progress
            goals = (await db.execute(
                select(Goal).where(Goal.space_id == space.id, Goal.status == "behind")
            )).scalars().all()
            if goals:
                suggestions.append(f"{len(goals)} goal(s) are behind schedule.")

    if not suggestions:
        suggestions = ["How can I help you today?", "Try asking about your project status."]

    return {"data": {"suggestions": suggestions}, "meta": {}, "errors": []}


async def _build_context(db: AsyncSession, space_key: str | None, user: dict) -> str:
    """Build context string from current space data."""
    if not space_key:
        return "No space selected."

    result = await db.execute(select(Space).where(Space.key == space_key.upper()))
    space = result.scalar_one_or_none()
    if not space:
        return f"Space '{space_key}' not found."

    # Counts
    item_count = (await db.execute(
        select(func.count()).select_from(WorkItem).where(WorkItem.space_id == space.id)
    )).scalar() or 0

    sprint_result = await db.execute(
        select(Sprint).where(Sprint.space_id == space.id, Sprint.status == "active")
    )
    active_sprint = sprint_result.scalar_one_or_none()

    budget_result = await db.execute(
        select(func.sum(Budget.total_amount), func.sum(Budget.spent_amount))
        .where(Budget.space_id == space.id)
    )
    budget_row = budget_result.fetchone()

    parts = [f"Space: {space.name} ({space.key}), template: {space.template}, {item_count} work items."]
    if active_sprint:
        parts.append(f"Active sprint: {active_sprint.name}")
    if budget_row and budget_row[0]:
        parts.append(f"Budget: {budget_row[1] or 0:,.0f} / {budget_row[0]:,.0f} spent")

    return "\n".join(parts)


def _generate_suggestions(message: str) -> list[str]:
    """Generate quick-reply suggestions based on user message."""
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["status", "progress", "how"]):
        return ["Show overdue items", "Sprint progress", "Goal status"]
    if any(w in msg_lower for w in ["create", "new", "add"]):
        return ["Create a task", "Start a sprint", "Add a goal"]
    if any(w in msg_lower for w in ["budget", "cost", "spend"]):
        return ["Budget summary", "Generate invoice", "Cost breakdown"]
    return ["Project overview", "My tasks", "Help"]
