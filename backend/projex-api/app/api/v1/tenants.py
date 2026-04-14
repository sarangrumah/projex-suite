"""Tenant provisioning + SaaS billing API."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.plan import Billing, Plan, Subscription, SystemConfig
from app.models.tenant import Tenant

router = APIRouter(tags=["tenants"])


class TenantCreate(BaseModel):
    model_config = ConfigDict()
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=63, pattern=r"^[a-z0-9\-]+$")
    plan_name: str = Field(default="free")


# ── Plans ───────────────────────────────────────────────────

@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(Plan).where(Plan.is_active == True).order_by(Plan.position)  # noqa: E712
    )
    plans = list(result.scalars().all())
    return {
        "data": [
            {"id": str(p.id), "name": p.name, "display_name": p.display_name,
             "price_monthly": p.price_monthly, "price_yearly": p.price_yearly,
             "currency": p.currency, "features": p.features, "limits": p.limits}
            for p in plans
        ],
        "meta": {}, "errors": [],
    }


# ── Tenant Provisioning ────────────────────────────────────

@router.post("/tenants", status_code=201)
async def provision_tenant(
    request: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Provision a new tenant with schema and subscription."""
    # Check slug unique
    existing = await db.execute(select(Tenant).where(Tenant.slug == request.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Tenant slug '{request.slug}' already exists")

    # Get plan
    plan_result = await db.execute(select(Plan).where(Plan.name == request.plan_name))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=400, detail=f"Plan '{request.plan_name}' not found")

    # Create tenant
    tenant = Tenant(name=request.name, slug=request.slug, plan=request.plan_name)
    db.add(tenant)
    await db.flush()

    # Create subscription
    today = date.today()
    trial_days_result = await db.execute(select(SystemConfig).where(SystemConfig.key == "trial_days"))
    trial_config = trial_days_result.scalar_one_or_none()
    trial_days = int(trial_config.value) if trial_config else 14

    sub = Subscription(
        tenant_id=tenant.id, plan_id=plan.id,
        status="trial" if plan.name == "free" else "active",
        current_period_start=today,
        current_period_end=today + timedelta(days=30),
        trial_end=today + timedelta(days=trial_days) if plan.name == "free" else None,
    )
    db.add(sub)

    # Create tenant schema
    from sqlalchemy import text
    schema = f"tenant_{request.slug}"
    await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

    await db.commit()
    await db.refresh(tenant)

    return {
        "data": {
            "id": str(tenant.id), "name": tenant.name, "slug": tenant.slug,
            "plan": request.plan_name, "schema": schema,
        },
        "meta": {}, "errors": [],
    }


# ── Subscription ────────────────────────────────────────────

@router.get("/tenants/{tenant_slug}/subscription")
async def get_subscription(
    tenant_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    tenant_result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    sub_result = await db.execute(
        select(Subscription).where(Subscription.tenant_id == tenant.id).order_by(Subscription.created_at.desc())
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        return {"data": None, "meta": {}, "errors": []}

    plan_result = await db.execute(select(Plan).where(Plan.id == sub.plan_id))
    plan = plan_result.scalar_one_or_none()

    return {
        "data": {
            "id": str(sub.id), "status": sub.status, "billing_cycle": sub.billing_cycle,
            "current_period_start": sub.current_period_start.isoformat(),
            "current_period_end": sub.current_period_end.isoformat(),
            "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
            "plan": {"name": plan.name, "display_name": plan.display_name, "features": plan.features} if plan else None,
        },
        "meta": {}, "errors": [],
    }


# ── System Config ───────────────────────────────────────────

@router.get("/system/config")
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(SystemConfig))
    configs = list(result.scalars().all())
    return {
        "data": {c.key: c.value for c in configs},
        "meta": {}, "errors": [],
    }
