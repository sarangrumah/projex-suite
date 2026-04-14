"""Add wiki_pages and wiki_page_versions tables.

Revision ID: 005_wiki
Revises: 004_custom_fields
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "005_wiki"
down_revision: Union[str, None] = "004_custom_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wiki_pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("wiki_pages.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False),
        sa.Column("body", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_wiki_space", "wiki_pages", ["space_id"])
    op.create_index("idx_wiki_slug", "wiki_pages", ["slug"])

    op.create_table(
        "wiki_page_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("page_id", UUID(as_uuid=True), sa.ForeignKey("wiki_pages.id"), nullable=False),
        sa.Column("version_num", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", JSONB(), nullable=False),
        sa.Column("edited_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_wiki_ver_page", "wiki_page_versions", ["page_id"])


def downgrade() -> None:
    op.drop_table("wiki_page_versions")
    op.drop_table("wiki_pages")
