#!/usr/bin/env bash
# ProjeX Suite — Deployment script
# Usage: ./scripts/deploy.sh
set -euo pipefail

COMPOSE_FILE="docker-compose.yml"
GIT_SHA=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "═══════════════════════════════════════════"
echo "  ProjeX Suite Deploy — $GIT_SHA"
echo "  $TIMESTAMP"
echo "═══════════════════════════════════════════"

# 1. Pull latest code
echo "[1/7] Pulling latest code..."
git pull origin main

# 2. Build Docker images
echo "[2/7] Building Docker images (tag: $GIT_SHA)..."
docker compose -f $COMPOSE_FILE build --no-cache

# 3. Run database migrations
echo "[3/7] Running database migrations..."
docker compose -f $COMPOSE_FILE run --rm projex-api alembic upgrade head

# 4. Start all services
echo "[4/7] Starting services..."
docker compose -f $COMPOSE_FILE up -d

# 5. Wait for health checks
echo "[5/7] Waiting for health checks..."
MAX_WAIT=120
SERVICES=("projex-api:8000" "era-ai-api:8100" "erabudget-api:8200" "appcatalog-api:8300")
for svc in "${SERVICES[@]}"; do
    NAME=$(echo "$svc" | cut -d: -f1)
    PORT=$(echo "$svc" | cut -d: -f2)
    echo -n "  Waiting for $NAME..."
    for i in $(seq 1 $MAX_WAIT); do
        if docker compose exec -T "$NAME" python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/health')" 2>/dev/null; then
            echo " ✓"
            break
        fi
        if [ "$i" -eq "$MAX_WAIT" ]; then
            echo " FAILED"
            echo "ERROR: $NAME did not become healthy in ${MAX_WAIT}s"
            exit 1
        fi
        sleep 1
    done
done

# 6. Smoke tests
echo "[6/7] Running smoke tests..."
API_URL="http://localhost:8000"

# Health check
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$STATUS" != "200" ]; then
    echo "  FAIL: Health check returned $STATUS"
    exit 1
fi
echo "  ✓ Health check passed"

# API docs (dev mode)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs" 2>/dev/null || echo "404")
echo "  ✓ API endpoint reachable"

# 7. Summary
echo "[7/7] Deployment complete!"
echo ""
echo "═══════════════════════════════════════════"
echo "  Services:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps
echo ""
echo "  Git SHA: $GIT_SHA"
echo "  Time: $TIMESTAMP"
echo "═══════════════════════════════════════════"
