"""Add SaaS billing tables (plans, subscriptions, billing, system_config) + automations.

Revision ID: 012_saas_billing
Revises: 011_files_links
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "012_saas_billing"
down_revision: Union[str, None] = "011_files_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Public schema: SaaS billing ─────────────────────────
    op.create_table("plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("price_monthly", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_yearly", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column("features", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("limits", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="public",
    )

    op.create_table("subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("public.tenants.id"), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("public.plans.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("billing_cycle", sa.String(10), nullable=False, server_default="monthly"),
        sa.Column("current_period_start", sa.Date(), nullable=False),
        sa.Column("current_period_end", sa.Date(), nullable=False),
        sa.Column("trial_end", sa.Date(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="public",
    )
    op.create_index("idx_sub_tenant", "subscriptions", ["tenant_id"], schema="public")

    op.create_table("billing",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("public.tenants.id"), nullable=False),
        sa.Column("subscription_id", UUID(as_uuid=True), sa.ForeignKey("public.subscriptions.id"), nullable=False),
        sa.Column("invoice_number", sa.String(50), unique=True, nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="public",
    )
    op.create_index("idx_bill_tenant", "billing", ["tenant_id"], schema="public")

    op.create_table("system_config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.String(2000), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="public",
    )

    # Seed default plans
    op.execute("""
        INSERT INTO public.plans (name, display_name, price_monthly, price_yearly, features, limits, position) VALUES
        ('free', 'Free', 0, 0, '{"max_users": 5, "max_spaces": 3, "max_storage_gb": 1, "ai_enabled": false, "whatsapp": false}', '{"api_rate_limit": 100}', 0),
        ('standard', 'Standard', 299000, 2990000, '{"max_users": 25, "max_spaces": 10, "max_storage_gb": 10, "ai_enabled": true, "whatsapp": false}', '{"api_rate_limit": 1000}', 1),
        ('premium', 'Premium', 799000, 7990000, '{"max_users": 100, "max_spaces": 50, "max_storage_gb": 100, "ai_enabled": true, "whatsapp": true}', '{"api_rate_limit": 5000}', 2),
        ('enterprise', 'Enterprise', 0, 0, '{"max_users": -1, "max_spaces": -1, "max_storage_gb": -1, "ai_enabled": true, "whatsapp": true}', '{"api_rate_limit": -1}', 3)
    """)

    # Seed default system config
    op.execute("""
        INSERT INTO public.system_config (key, value, description) VALUES
        ('app_name', 'ProjeX Suite', 'Application display name'),
        ('default_plan', 'free', 'Default plan for new tenants'),
        ('trial_days', '14', 'Free trial period in days'),
        ('tax_rate', '11', 'PPN tax rate percentage'),
        ('maintenance_mode', 'false', 'Enable maintenance mode')
    """)

    # ── Tenant schema: automations ──────────────────────────
    op.create_table("automations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("trigger_type", sa.String(30), nullable=False),
        sa.Column("trigger_config", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("action_config", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_auto_space", "automations", ["space_id"])


def downgrade() -> None:
    op.drop_table("automations")
    op.drop_table("system_config", schema="public")
    op.drop_table("billing", schema="public")
    op.drop_table("subscriptions", schema="public")
    op.drop_table("plans", schema="public")
