"""Automation model — when-trigger rules per space."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Automation(Base):
    """An automation rule: when X happens, do Y."""

    __tablename__ = "automations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # status_changed, item_created, item_assigned, due_date_passed, sprint_started, sprint_closed
    trigger_config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    # e.g. {"from_status": "In Progress", "to_status": "Done"}
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # assign_user, change_status, send_notification, add_comment, move_to_sprint, webhook
    action_config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    # e.g. {"assign_to": "user-id"} or {"webhook_url": "https://..."}
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
