"""Add spaces, workflows, sprints, work_items, comments, worklogs tables.

Revision ID: 002_spaces_items
Revises: 001_initial
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision: str = "002_spaces_items"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Spaces ──────────────────────────────────────────────
    op.create_table(
        "spaces",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key", sa.String(10), unique=True, nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("template", sa.String(20), nullable=False, server_default="blank"),
        sa.Column("management_mode", sa.String(20), nullable=False, server_default="team"),
        sa.Column("settings", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("nav_tabs", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("item_sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_spaces_key", "spaces", ["key"], unique=True)

    # ── Workflows ───────────────────────────────────────────
    op.create_table(
        "workflows",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("name", sa.String(127), nullable=False),
        sa.Column("work_item_type", sa.String(63), nullable=False, server_default="task"),
        sa.Column("definition", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Workflow Statuses ───────────────────────────────────
    op.create_table(
        "workflow_statuses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("name", sa.String(63), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6B7280"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Sprints ─────────────────────────────────────────────
    op.create_table(
        "sprints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("name", sa.String(127), nullable=False),
        sa.Column("goal", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_sprints_space", "sprints", ["space_id"])

    # ── Work Items ──────────────────────────────────────────
    op.create_table(
        "work_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("key", sa.String(20), unique=True, nullable=False),
        sa.Column("sequence_num", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(63), nullable=False, server_default="task"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", JSONB(), nullable=True),
        sa.Column("status_id", UUID(as_uuid=True), sa.ForeignKey("workflow_statuses.id"), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("assignee_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reporter_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("work_items.id"), nullable=True),
        sa.Column("sprint_id", UUID(as_uuid=True), sa.ForeignKey("sprints.id"), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("estimate_points", sa.Float(), nullable=True),
        sa.Column("estimate_hours", sa.Float(), nullable=True),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("labels", ARRAY(sa.String()), nullable=True),
        sa.Column("custom_fields", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_wi_space_status", "work_items", ["space_id", "status_id"])
    op.create_index("idx_wi_assignee", "work_items", ["assignee_id"])
    op.create_index("idx_wi_sprint", "work_items", ["sprint_id"])
    op.create_index("idx_wi_parent", "work_items", ["parent_id"])

    # ── Comments ────────────────────────────────────────────
    op.create_table(
        "comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("work_item_id", UUID(as_uuid=True), sa.ForeignKey("work_items.id"), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("comments.id"), nullable=True),
        sa.Column("body", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_comments_item", "comments", ["work_item_id"])

    # ── Worklogs ────────────────────────────────────────────
    op.create_table(
        "worklogs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("work_item_id", UUID(as_uuid=True), sa.ForeignKey("work_items.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_worklogs_item", "worklogs", ["work_item_id"])


def downgrade() -> None:
    op.drop_table("worklogs")
    op.drop_table("comments")
    op.drop_table("work_items")
    op.drop_table("sprints")
    op.drop_table("workflow_statuses")
    op.drop_table("workflows")
    op.drop_table("spaces")
