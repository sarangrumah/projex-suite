"""Add audit schema with hash-chained events table.

Revision ID: 003_audit
Revises: 002_spaces_items
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "003_audit"
down_revision: Union[str, None] = "002_spaces_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit schema
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    # Audit events — append-only, hash-chained
    op.create_table(
        "events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("prev_hash", sa.String(64), nullable=True),
        sa.Column("entry_hash", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("actor_ip", sa.String(45), nullable=False),
        sa.Column("action", sa.String(63), nullable=False),
        sa.Column("resource_type", sa.String(63), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=False),
        sa.Column("tenant_id", sa.String(63), nullable=True),
        sa.Column("before_state", JSONB(), nullable=True),
        sa.Column("after_state", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="audit",
    )
    op.create_index("idx_audit_hash", "events", ["entry_hash"], schema="audit")
    op.create_index("idx_audit_resource", "events", ["resource_type", "resource_id"], schema="audit")
    op.create_index("idx_audit_actor", "events", ["actor_id"], schema="audit")
    op.create_index("idx_audit_created", "events", ["created_at"], schema="audit")

    # Revoke DELETE on audit.events — append-only
    op.execute("REVOKE DELETE ON audit.events FROM PUBLIC")


def downgrade() -> None:
    op.drop_table("events", schema="audit")
    op.execute("DROP SCHEMA IF EXISTS audit")
