"""Pydantic v2 schemas for Goals/OKR endpoints."""

from __future__ import annotations
from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    model_config = ConfigDict()
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    due_date: date | None = None


class GoalUpdate(BaseModel):
    model_config = ConfigDict()
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: str | None = Field(default=None, pattern=r"^(on_track|at_risk|behind|completed)$")
    start_date: date | None = None
    due_date: date | None = None


class KeyResultCreate(BaseModel):
    model_config = ConfigDict()
    title: str = Field(..., min_length=1, max_length=500)
    metric_type: str = Field(default="number", pattern=r"^(number|percent|currency|boolean)$")
    target_value: float = Field(..., gt=0)
    start_value: float = Field(default=0)
    unit: str | None = Field(default=None, max_length=20)


class KeyResultUpdate(BaseModel):
    model_config = ConfigDict()
    title: str | None = None
    current_value: float | None = None
    target_value: float | None = None
