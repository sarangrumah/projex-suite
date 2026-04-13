"""Comment model — threaded comments on work items."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Comment(Base):
    """A comment on a work item — supports threading via parent_id."""

    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    work_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True
    )  # For threaded replies
    body: Mapped[dict] = mapped_column(JSONB, nullable=False)  # TipTap rich text
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    work_item: Mapped["WorkItem"] = relationship(back_populates="comments")
    replies: Mapped[list["Comment"]] = relationship(back_populates="parent_comment")
    parent_comment: Mapped["Comment | None"] = relationship(
        back_populates="replies", remote_side=[id]
    )


from app.models.work_item import WorkItem  # noqa: E402, F811
