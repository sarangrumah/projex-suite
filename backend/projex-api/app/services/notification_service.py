"""Notification service — create, list, mark read."""

from __future__ import annotations
from uuid import UUID
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: UUID, type: str, title: str, body: str | None = None,
                     link: str | None = None, extra: dict | None = None) -> Notification:
        notif = Notification(user_id=user_id, type=type, title=title, body=body, link=link, extra=extra or {})
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def list_for_user(self, user_id: UUID, unread_only: bool = False, limit: int = 50) -> list[Notification]:
        q = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.is_read == False)  # noqa: E712
        q = q.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def unread_count(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        )
        return result.scalar() or 0

    async def mark_read(self, notif_id: UUID, user_id: UUID) -> None:
        await self.db.execute(
            update(Notification).where(Notification.id == notif_id, Notification.user_id == user_id)
            .values(is_read=True)
        )
        await self.db.commit()

    async def mark_all_read(self, user_id: UUID) -> int:
        result = await self.db.execute(
            update(Notification).where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount
