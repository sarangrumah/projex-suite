"""Workflow and WorkflowStatus models — define status columns and transitions."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Workflow(Base):
    """Visual workflow definition for a space + work item type."""

    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(127), nullable=False)
    work_item_type: Mapped[str] = mapped_column(
        String(63), nullable=False, server_default="task"
    )  # Which item types use this workflow
    definition: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # { transitions: [{ from, to, conditions, validators, post_functions }] }
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    space: Mapped["Space"] = relationship(back_populates="workflows")
    statuses: Mapped[list["WorkflowStatus"]] = relationship(
        back_populates="workflow", order_by="WorkflowStatus.position"
    )


class WorkflowStatus(Base):
    """A single status node within a workflow."""

    __tablename__ = "workflow_statuses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(63), nullable=False)
    category: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # todo | in_progress | done
    color: Mapped[str] = mapped_column(String(7), nullable=False, server_default="#6B7280")
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="statuses")


# Resolve forward reference
from app.models.space import Space  # noqa: E402, F811
