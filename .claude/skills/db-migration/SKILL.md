---
name: db-migration
description: Database migration patterns for ProjeX Suite using Alembic with schema-per-tenant PostgreSQL. Use when creating tables, modifying schema, adding indexes, or managing tenant provisioning.
allowed-tools: Read, Write, Edit, Bash, Grep
---

# Database Migration Patterns (Alembic + Schema-per-Tenant)

## Create Migration

```bash
# Auto-generate from model changes
cd backend/projex-api
alembic revision --autogenerate -m "add_work_items_table"

# Manual migration
alembic revision -m "add_custom_index"
```

## Migration Template (Tenant Schema)

```python
"""add work_items table

Revision ID: abc123
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # This runs against EVERY tenant schema
    op.create_table(
        "work_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("key", sa.String(20), nullable=False),
        sa.Column("sequence_num", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(63), nullable=False, server_default="task"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", JSONB(), nullable=True),
        sa.Column("status_id", UUID(as_uuid=True), sa.ForeignKey("workflow_statuses.id")),
        sa.Column("priority", sa.String(20), server_default="normal"),
        sa.Column("assignee_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("work_items.id")),
        sa.Column("sprint_id", UUID(as_uuid=True), sa.ForeignKey("sprints.id")),
        sa.Column("custom_fields", JSONB(), server_default="{}"),
        sa.Column("position", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("space_id", "key"),
    )
    op.create_index("idx_wi_space_status", "work_items", ["space_id", "status_id"])
    op.create_index("idx_wi_assignee", "work_items", ["assignee_id"])
    op.create_index("idx_wi_sprint", "work_items", ["sprint_id"])

def downgrade():
    op.drop_table("work_items")
```

## Multi-Tenant Migration Runner

```python
# alembic/env.py — run migrations across all tenant schemas
from app.core.database import get_all_tenant_schemas

def run_migrations_online():
    connectable = engine_from_config(config.get_section("alembic"))
    
    with connectable.connect() as connection:
        # 1. Run on public schema (shared tables)
        context.configure(connection=connection, target_metadata=target_metadata,
                          version_table_schema="public")
        with context.begin_transaction():
            context.run_migrations()
        
        # 2. Run on each tenant schema
        for schema in get_all_tenant_schemas(connection):
            connection.execute(text(f"SET search_path TO {schema}"))
            context.configure(connection=connection, target_metadata=target_metadata,
                              version_table_schema=schema)
            with context.begin_transaction():
                context.run_migrations()
```

## Tenant Provisioning

```python
async def create_tenant_schema(db: AsyncSession, tenant_slug: str):
    """Create new tenant schema from template."""
    schema = f"tenant_{tenant_slug}"
    await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    await db.execute(text(f"SET search_path TO {schema}"))
    # Run all migrations on new schema
    # This creates all tables in the new tenant schema
    await run_alembic_upgrade(schema)
```

## CRITICAL RULES
- NEVER modify existing columns directly — add new, migrate data, drop old
- ALWAYS make migrations backward-compatible (no breaking changes)
- ALWAYS test migration on staging before production
- ALWAYS include downgrade() function
- NEVER use raw SQL in app code — migrations are the only exception
- ALWAYS add indexes for columns used in WHERE, JOIN, ORDER BY
- ALWAYS run `alembic upgrade head` before `alembic revision --autogenerate`
