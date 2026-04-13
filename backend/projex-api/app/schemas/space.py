"""Pydantic v2 schemas for Space endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SpaceCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(..., min_length=1, max_length=255)
    key: str | None = Field(
        default=None, min_length=2, max_length=10, pattern=r"^[A-Z][A-Z0-9]*$"
    )  # Auto-generated from name if omitted
    description: str | None = Field(default=None, max_length=2000)
    template: str = Field(default="blank", pattern=r"^(scrum|kanban|bug|blank)$")
    management_mode: str = Field(default="team", pattern=r"^(company|team)$")


class SpaceUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    settings: dict | None = None
    nav_tabs: list[str] | None = None


class SpaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key: str
    description: str | None
    template: str
    management_mode: str
    status: str
    created_at: datetime
