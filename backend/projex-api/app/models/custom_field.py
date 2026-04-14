"""CustomFieldDefinition model — field registry for spaces."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CustomFieldDefinition(Base):
    """Defines a custom field that can be added to work items in a space.

    Supported types:
    - text: single-line string
    - textarea: multi-line string
    - number: integer or float
    - date: date value
    - select: single choice from options
    - multi_select: multiple choices from options
    - checkbox: boolean
    - url: URL string
    - user: user reference (UUID)
    - formula: computed from other fields (read-only)
    - rollup: aggregated from child items (read-only)
    """

    __tablename__ = "custom_field_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(127), nullable=False)
    field_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # Type-specific config: options (select), formula expression, rollup config
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
