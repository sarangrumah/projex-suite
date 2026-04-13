"""Space model — project container within a tenant schema."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Space(Base):
    """A project space (like a Jira project) — container for work items."""

    __tablename__ = "spaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )  # Uppercase, 2-10 chars (e.g. "AIM")
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    template: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="blank"
    )  # scrum | kanban | bug | blank
    management_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="team"
    )  # company | team
    settings: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    nav_tabs: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # Array of enabled tabs
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="active"
    )  # active | archived
    item_sequence: Mapped[int] = mapped_column(
        nullable=False, server_default="0"
    )  # Auto-increment counter for work item keys
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    workflows: Mapped[list["Workflow"]] = relationship(back_populates="space")
    work_items: Mapped[list["WorkItem"]] = relationship(back_populates="space")


# Avoid circular import — these are resolved at runtime
from app.models.workflow import Workflow  # noqa: E402
from app.models.work_item import WorkItem  # noqa: E402
