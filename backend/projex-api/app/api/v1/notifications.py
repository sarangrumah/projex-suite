"""Notification API endpoints."""

from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/")
async def list_notifications(
    unread_only: bool = False, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = NotificationService(db)
    notifs = await service.list_for_user(UUID(current_user["sub"]), unread_only)
    count = await service.unread_count(UUID(current_user["sub"]))
    return {
        "data": [
            {"id": str(n.id), "type": n.type, "title": n.title, "body": n.body,
             "link": n.link, "is_read": n.is_read, "created_at": n.created_at.isoformat()}
            for n in notifs
        ],
        "meta": {"unread_count": count}, "errors": [],
    }

@router.put("/{notif_id}/read")
async def mark_read(
    notif_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = NotificationService(db)
    await service.mark_read(UUID(notif_id), UUID(current_user["sub"]))
    return {"data": {"marked": True}, "meta": {}, "errors": []}

@router.put("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = NotificationService(db)
    count = await service.mark_all_read(UUID(current_user["sub"]))
    return {"data": {"marked": count}, "meta": {}, "errors": []}
