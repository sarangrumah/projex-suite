"""Pydantic v2 schemas for WorkItem, Comment, and Worklog endpoints."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Work Items ──────────────────────────────────────────────

class ItemCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    title: str = Field(..., min_length=1, max_length=500)
    type: str = Field(default="task", pattern=r"^(epic|story|task|bug|sub_task|cr)$")
    description: dict | None = None  # TipTap JSON
    priority: str = Field(default="normal", pattern=r"^(critical|high|normal|low)$")
    assignee_id: UUID | None = None
    parent_id: UUID | None = None
    sprint_id: UUID | None = None
    due_date: date | None = None
    start_date: date | None = None
    estimate_points: float | None = None
    estimate_hours: float | None = None
    labels: list[str] | None = None


class ItemUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: dict | None = None
    status_id: UUID | None = None
    priority: str | None = Field(default=None, pattern=r"^(critical|high|normal|low)$")
    assignee_id: UUID | None = None
    parent_id: UUID | None = None
    sprint_id: UUID | None = None
    due_date: date | None = None
    start_date: date | None = None
    estimate_points: float | None = None
    estimate_hours: float | None = None
    labels: list[str] | None = None
    position: int | None = None
    custom_fields: dict | None = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    type: str
    title: str
    status_id: UUID | None
    priority: str
    assignee_id: UUID | None
    parent_id: UUID | None
    sprint_id: UUID | None
    position: int
    created_at: datetime
    updated_at: datetime


class ItemMoveRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    status_id: UUID
    position: int = 0
    sprint_id: UUID | None = None


# ── Comments ────────────────────────────────────────────────

class CommentCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    body: dict  # TipTap JSON
    parent_id: UUID | None = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_item_id: UUID
    author_id: UUID
    parent_id: UUID | None
    body: dict
    created_at: datetime


# ── Worklogs ────────────────────────────────────────────────

class WorklogCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    time_spent_seconds: int = Field(..., gt=0)
    description: str | None = Field(default=None, max_length=1000)
    log_date: date


class WorklogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_item_id: UUID
    user_id: UUID
    time_spent_seconds: int
    description: str | None
    log_date: date
    created_at: datetime
