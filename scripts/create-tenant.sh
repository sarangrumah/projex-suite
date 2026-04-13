#!/usr/bin/env bash
# Create a new tenant with its own schema
# Usage: ./scripts/create-tenant.sh <slug> <name>
set -euo pipefail

SLUG=${1:?"Usage: create-tenant.sh <slug> <name>"}
NAME=${2:?"Usage: create-tenant.sh <slug> <name>"}

echo "Creating tenant: $NAME (slug: $SLUG)"

docker compose exec -T postgres psql -U "${POSTGRES_USER:-projex}" -d "${POSTGRES_DB:-projex}" <<SQL
-- Create tenant record
INSERT INTO public.tenants (name, slug, plan, is_active)
VALUES ('$NAME', '$SLUG', 'free', true)
ON CONFLICT (slug) DO NOTHING;

-- Create tenant schema
CREATE SCHEMA IF NOT EXISTS tenant_$SLUG;

-- Apply tables to tenant schema
SET search_path TO tenant_$SLUG;
SQL

# Run migrations on the new schema
docker compose run --rm projex-api alembic upgrade head

echo "✓ Tenant '$SLUG' created successfully"
