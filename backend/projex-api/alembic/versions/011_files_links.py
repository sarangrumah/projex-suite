"""Add files and work_item_links tables.

Revision ID: 011_files_links
Revises: 010_notifications
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "011_files_links"
down_revision: Union[str, None] = "010_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("files",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("work_item_id", UUID(as_uuid=True), sa.ForeignKey("work_items.id"), nullable=True),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(127), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_files_item", "files", ["work_item_id"])

    op.create_table("work_item_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("work_items.id"), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), sa.ForeignKey("work_items.id"), nullable=False),
        sa.Column("link_type", sa.String(20), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_link_source", "work_item_links", ["source_id"])
    op.create_index("idx_link_target", "work_item_links", ["target_id"])

def downgrade() -> None:
    op.drop_table("work_item_links")
    op.drop_table("files")
