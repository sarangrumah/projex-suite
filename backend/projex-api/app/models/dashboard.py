"""Dashboard and Widget models — configurable dashboards per space."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dashboard(Base):
    """A configurable dashboard within a space."""

    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    widgets: Mapped[list[DashboardWidget]] = relationship(back_populates="dashboard", order_by="DashboardWidget.position")


class DashboardWidget(Base):
    """A widget instance on a dashboard."""

    __tablename__ = "dashboard_widgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dashboards.id"), nullable=False, index=True)
    widget_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # Types: item_count, status_breakdown, priority_chart, recent_activity, burndown, budget_summary, goal_progress
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    size: Mapped[str] = mapped_column(String(10), nullable=False, server_default="medium")  # small | medium | large
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    dashboard: Mapped[Dashboard] = relationship(back_populates="widgets")
