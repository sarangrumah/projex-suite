"""Audit event model — immutable, hash-chained log in the audit schema."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditEvent(Base):
    """Immutable audit log entry with hash-chain integrity."""

    __tablename__ = "events"
    __table_args__ = {"schema": "audit"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Actor
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_ip: Mapped[str] = mapped_column(String(45), nullable=False)

    # Action
    action: Mapped[str] = mapped_column(String(63), nullable=False)  # create | update | delete
    resource_type: Mapped[str] = mapped_column(String(63), nullable=False)  # user | space | work_item
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(63), nullable=True)

    # State
    before_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
