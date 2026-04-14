"""Pydantic v2 schemas for Custom Field endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

VALID_TYPES = ("text", "textarea", "number", "date", "select", "multi_select",
               "checkbox", "url", "user", "formula", "rollup")


class CustomFieldCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(..., min_length=1, max_length=127)
    field_type: str = Field(..., pattern=r"^(text|textarea|number|date|select|multi_select|checkbox|url|user|formula|rollup)$")
    description: str | None = Field(default=None, max_length=500)
    is_required: bool = False
    config: dict = Field(default_factory=dict)
    # config examples:
    # select/multi_select: {"options": ["Option A", "Option B"]}
    # formula: {"expression": "estimate_hours * 100", "result_type": "number"}
    # rollup: {"source_field": "estimate_points", "aggregation": "sum", "child_type": "story"}


class CustomFieldUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=1, max_length=127)
    description: str | None = Field(default=None, max_length=500)
    is_required: bool | None = None
    position: int | None = None
    config: dict | None = None


class CustomFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    space_id: UUID
    name: str
    field_type: str
    description: str | None
    is_required: bool
    position: int
    config: dict
    created_at: datetime
