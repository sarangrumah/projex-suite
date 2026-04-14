"""Budget API endpoints: budgets, line items, invoices."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, InvoiceCreate, InvoiceUpdate, LineItemCreate,
)
from app.services.budget_service import BudgetService

router = APIRouter(tags=["budgets"])


@router.post("/spaces/{space_key}/budgets", status_code=status.HTTP_201_CREATED)
async def create_budget(
    space_key: str, request: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.BUDGET_CREATE)),
) -> dict:
    service = BudgetService(db)
    try:
        b = await service.create_budget(space_key.upper(), request, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _budget_dict(b), "meta": {}, "errors": []}


@router.get("/spaces/{space_key}/budgets")
async def list_budgets(
    space_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.BUDGET_VIEW)),
) -> dict:
    service = BudgetService(db)
    try:
        budgets = await service.list_budgets(space_key.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": [_budget_dict(b) for b in budgets], "meta": {}, "errors": []}


@router.get("/budgets/{budget_id}")
async def get_budget(
    budget_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.BUDGET_VIEW)),
) -> dict:
    service = BudgetService(db)
    b = await service.get_budget(UUID(budget_id))
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found")
    items = await service.list_line_items(b.id)
    invoices = await service.list_invoices(b.id)
    data = _budget_dict(b)
    data["line_items"] = [_line_dict(li) for li in items]
    data["invoices"] = [_invoice_dict(inv) for inv in invoices]
    return {"data": data, "meta": {}, "errors": []}


@router.put("/budgets/{budget_id}")
async def update_budget(
    budget_id: str, request: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.BUDGET_EDIT)),
) -> dict:
    service = BudgetService(db)
    try:
        b = await service.update_budget(UUID(budget_id), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _budget_dict(b), "meta": {}, "errors": []}


# ── Line Items ──────────────────────────────────────────────

@router.post("/budgets/{budget_id}/items", status_code=status.HTTP_201_CREATED)
async def add_line_item(
    budget_id: str, request: LineItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.BUDGET_EDIT)),
) -> dict:
    service = BudgetService(db)
    try:
        li = await service.add_line_item(UUID(budget_id), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _line_dict(li), "meta": {}, "errors": []}


# ── Invoices ────────────────────────────────────────────────

@router.post("/budgets/{budget_id}/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    budget_id: str, request: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.BUDGET_CREATE)),
) -> dict:
    service = BudgetService(db)
    try:
        inv = await service.create_invoice(UUID(budget_id), request, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _invoice_dict(inv), "meta": {}, "errors": []}


@router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: str, request: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.BUDGET_EDIT)),
) -> dict:
    service = BudgetService(db)
    try:
        inv = await service.update_invoice(UUID(invoice_id), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": _invoice_dict(inv), "meta": {}, "errors": []}


# ── Serializers ─────────────────────────────────────────────

def _budget_dict(b) -> dict:  # noqa: ANN001
    return {
        "id": str(b.id), "name": b.name, "description": b.description,
        "currency": b.currency, "total_amount": b.total_amount,
        "spent_amount": b.spent_amount, "remaining": b.total_amount - b.spent_amount,
        "status": b.status,
        "start_date": b.start_date.isoformat() if b.start_date else None,
        "end_date": b.end_date.isoformat() if b.end_date else None,
        "created_at": b.created_at.isoformat(),
    }

def _line_dict(li) -> dict:  # noqa: ANN001
    return {
        "id": str(li.id), "category": li.category, "description": li.description,
        "quantity": li.quantity, "unit_price": li.unit_price,
        "total_price": li.total_price, "position": li.position,
    }

def _invoice_dict(inv) -> dict:  # noqa: ANN001
    return {
        "id": str(inv.id), "invoice_number": inv.invoice_number,
        "amount": inv.amount, "tax_amount": inv.tax_amount,
        "total_amount": inv.total_amount, "status": inv.status,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "paid_date": inv.paid_date.isoformat() if inv.paid_date else None,
        "notes": inv.notes, "created_at": inv.created_at.isoformat(),
    }
