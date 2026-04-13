"""WorkItem model — core entity: epics, stories, tasks, bugs, sub-tasks."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WorkItem(Base):
    """A work item (epic/story/task/bug/sub-task) within a space."""

    __tablename__ = "work_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )  # e.g. "AIM-101"
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)

    # Type & content
    type: Mapped[str] = mapped_column(
        String(63), nullable=False, server_default="task"
    )  # epic | story | task | bug | sub_task | cr
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # TipTap format

    # Status & priority
    status_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_statuses.id"), nullable=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="normal"
    )  # critical | high | normal | low

    # Assignments
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Hierarchy
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True, index=True
    )

    # Sprint
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sprints.id"), nullable=True, index=True
    )

    # Planning
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimate_points: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimate_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # Metadata
    labels: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    space: Mapped["Space"] = relationship(back_populates="work_items")
    children: Mapped[list["WorkItem"]] = relationship(back_populates="parent")
    parent: Mapped["WorkItem | None"] = relationship(
        back_populates="children", remote_side=[id]
    )
    comments: Mapped[list["Comment"]] = relationship(back_populates="work_item")
    worklogs: Mapped[list["Worklog"]] = relationship(back_populates="work_item")


from app.models.space import Space  # noqa: E402, F811
from app.models.comment import Comment  # noqa: E402
from app.models.worklog import Worklog  # noqa: E402
