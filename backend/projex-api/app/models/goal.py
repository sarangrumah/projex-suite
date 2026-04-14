"""Goal and KeyResult models — OKR tracking per space."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Goal(Base):
    """An OKR objective within a space."""

    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="on_track")  # on_track | at_risk | behind | completed
    progress: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")  # 0-100
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    key_results: Mapped[list[KeyResult]] = relationship(back_populates="goal")


class KeyResult(Base):
    """A measurable key result under a goal."""

    __tablename__ = "key_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="number")  # number | percent | currency | boolean
    current_value: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    start_value: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "users", "Rp", "%"
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    goal: Mapped[Goal] = relationship(back_populates="key_results")
