"""Budget service — CRUD for budgets, line items, invoices."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget, BudgetLineItem, Invoice
from app.models.space import Space
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, InvoiceCreate, InvoiceUpdate, LineItemCreate,
)


class BudgetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Budget CRUD ─────────────────────────────────────────

    async def create_budget(self, space_key: str, data: BudgetCreate, user_id: UUID) -> Budget:
        space = await self._get_space(space_key)
        budget = Budget(
            space_id=space.id,
            name=data.name,
            description=data.description,
            currency=data.currency,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=user_id,
        )
        self.db.add(budget)
        await self.db.commit()
        await self.db.refresh(budget)
        return budget

    async def list_budgets(self, space_key: str) -> list[Budget]:
        space = await self._get_space(space_key)
        result = await self.db.execute(
            select(Budget).where(Budget.space_id == space.id).order_by(Budget.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_budget(self, budget_id: UUID) -> Budget | None:
        result = await self.db.execute(select(Budget).where(Budget.id == budget_id))
        return result.scalar_one_or_none()

    async def update_budget(self, budget_id: UUID, data: BudgetUpdate) -> Budget:
        budget = await self.get_budget(budget_id)
        if not budget:
            raise ValueError("Budget not found")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(budget, k, v)
        budget.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(budget)
        return budget

    # ── Line Items ──────────────────────────────────────────

    async def add_line_item(self, budget_id: UUID, data: LineItemCreate) -> BudgetLineItem:
        budget = await self.get_budget(budget_id)
        if not budget:
            raise ValueError("Budget not found")

        total_price = data.quantity * data.unit_price
        count_q = select(func.count()).select_from(BudgetLineItem).where(
            BudgetLineItem.budget_id == budget_id
        )
        count = (await self.db.execute(count_q)).scalar() or 0

        item = BudgetLineItem(
            budget_id=budget_id,
            category=data.category,
            description=data.description,
            quantity=data.quantity,
            unit_price=data.unit_price,
            total_price=total_price,
            position=count,
        )
        self.db.add(item)

        # Update budget total
        budget.total_amount += total_price
        budget.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_line_items(self, budget_id: UUID) -> list[BudgetLineItem]:
        result = await self.db.execute(
            select(BudgetLineItem)
            .where(BudgetLineItem.budget_id == budget_id)
            .order_by(BudgetLineItem.position)
        )
        return list(result.scalars().all())

    # ── Invoices ────────────────────────────────────────────

    async def create_invoice(self, budget_id: UUID, data: InvoiceCreate, user_id: UUID) -> Invoice:
        budget = await self.get_budget(budget_id)
        if not budget:
            raise ValueError("Budget not found")

        tax_amount = data.amount * (data.tax_percent / 100)
        total = data.amount + tax_amount

        # Auto-generate invoice number
        count_q = select(func.count()).select_from(Invoice).where(Invoice.budget_id == budget_id)
        count = (await self.db.execute(count_q)).scalar() or 0
        inv_number = f"INV-{budget.name[:3].upper()}-{count + 1:04d}"

        invoice = Invoice(
            budget_id=budget_id,
            invoice_number=inv_number,
            amount=data.amount,
            tax_amount=tax_amount,
            total_amount=total,
            due_date=data.due_date,
            notes=data.notes,
            invoice_meta={"tax_percent": data.tax_percent},
            created_by=user_id,
        )
        self.db.add(invoice)

        # Update budget spent
        budget.spent_amount += total
        budget.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def list_invoices(self, budget_id: UUID) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.budget_id == budget_id).order_by(Invoice.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_invoice(self, invoice_id: UUID, data: InvoiceUpdate) -> Invoice:
        result = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise ValueError("Invoice not found")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(invoice, k, v)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def _get_space(self, key: str) -> Space:
        result = await self.db.execute(select(Space).where(Space.key == key))
        space = result.scalar_one_or_none()
        if not space:
            raise ValueError(f"Space '{key}' not found")
        return space
