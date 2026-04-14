"""Pydantic v2 schemas for Budget, LineItem, and Invoice endpoints."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    model_config = ConfigDict()
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    currency: str = Field(default="IDR", max_length=3)
    start_date: date | None = None
    end_date: date | None = None


class BudgetUpdate(BaseModel):
    model_config = ConfigDict()
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, pattern=r"^(draft|active|closed)$")
    start_date: date | None = None
    end_date: date | None = None


class LineItemCreate(BaseModel):
    model_config = ConfigDict()
    category: str = Field(..., min_length=1, max_length=127)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(..., ge=0)


class InvoiceCreate(BaseModel):
    model_config = ConfigDict()
    amount: float = Field(..., gt=0)
    tax_percent: float = Field(default=11, ge=0)  # PPN 11%
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class InvoiceUpdate(BaseModel):
    model_config = ConfigDict()
    status: str | None = Field(default=None, pattern=r"^(draft|sent|paid|overdue|cancelled)$")
    paid_date: date | None = None
    notes: str | None = None
