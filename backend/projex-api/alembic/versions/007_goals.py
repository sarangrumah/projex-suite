"""Add goals and key_results tables.

Revision ID: 007_goals
Revises: 006_budget
Create Date: 2026-04-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007_goals"
down_revision: Union[str, None] = "006_budget"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="on_track"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_goals_space", "goals", ["space_id"])

    op.create_table(
        "key_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("goal_id", UUID(as_uuid=True), sa.ForeignKey("goals.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("metric_type", sa.String(20), nullable=False, server_default="number"),
        sa.Column("current_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("start_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_kr_goal", "key_results", ["goal_id"])


def downgrade() -> None:
    op.drop_table("key_results")
    op.drop_table("goals")
