"""Pydantic v2 schemas for AppCatalog endpoints."""

from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    model_config = ConfigDict()
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class DocumentCreate(BaseModel):
    model_config = ConfigDict()
    doc_type: str = Field(..., pattern=r"^(brd|fsd|tsd|data_dict|api_spec|security)$")
    title: str = Field(..., min_length=1, max_length=500)
    body: dict = Field(default_factory=dict)
    code_ownership_map: dict = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    model_config = ConfigDict()
    title: str | None = None
    body: dict | None = None
    code_ownership_map: dict | None = None


class RepositoryCreate(BaseModel):
    model_config = ConfigDict()
    repo_url: str = Field(..., min_length=1, max_length=500)
    webhook_secret: str | None = None


class VersionApproval(BaseModel):
    model_config = ConfigDict()
    status: str = Field(..., pattern=r"^(approved|published)$")
