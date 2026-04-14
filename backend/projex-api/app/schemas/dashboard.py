"""Pydantic v2 schemas for Dashboard endpoints."""

from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DashboardCreate(BaseModel):
    model_config = ConfigDict()
    name: str = Field(..., min_length=1, max_length=255)


class WidgetCreate(BaseModel):
    model_config = ConfigDict()
    widget_type: str = Field(..., pattern=r"^(item_count|status_breakdown|priority_chart|recent_activity|budget_summary|goal_progress)$")
    title: str = Field(..., min_length=1, max_length=255)
    size: str = Field(default="medium", pattern=r"^(small|medium|large)$")
    config: dict = Field(default_factory=dict)
