"""Pydantic v2 schemas for Wiki endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WikiPageCreate(BaseModel):
    model_config = ConfigDict()

    title: str = Field(..., min_length=1, max_length=500)
    body: dict = Field(default_factory=dict)
    parent_id: UUID | None = None


class WikiPageUpdate(BaseModel):
    model_config = ConfigDict()

    title: str | None = Field(default=None, min_length=1, max_length=500)
    body: dict | None = None
    parent_id: UUID | None = None
    position: int | None = None


class WikiPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    space_id: UUID
    parent_id: UUID | None
    title: str
    slug: str
    body: dict
    position: int
    created_by: UUID
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime


class WikiPageListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None
    title: str
    slug: str
    position: int
    updated_at: datetime


class WikiVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    page_id: UUID
    version_num: int
    title: str
    body: dict
    edited_by: UUID
    created_at: datetime
