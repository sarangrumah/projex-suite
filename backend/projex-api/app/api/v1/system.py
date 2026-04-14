"""System API — health, metrics, readiness for production monitoring."""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.core.config import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    """Kubernetes/Docker readiness probe — checks DB + Redis connectivity."""
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis
    try:
        from redis.asyncio import from_url
        redis = from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
        checks["redis"] = "ok"
        await redis.aclose()
    except Exception:
        checks["redis"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values() if v != "unavailable")
    return {
        "data": {"ready": all_ok, "checks": checks, "version": settings.app_version},
        "meta": {}, "errors": [],
    }


@router.get("/info")
async def info() -> dict:
    """System info — non-sensitive metadata for monitoring."""
    return {
        "data": {
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
        "meta": {}, "errors": [],
    }
