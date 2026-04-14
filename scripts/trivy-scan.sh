#!/usr/bin/env bash
# Scan all Docker images for CVEs using Trivy
set -euo pipefail

SEVERITY="${1:-HIGH,CRITICAL}"

echo "Scanning ProjeX Suite Docker images (severity: $SEVERITY)..."
echo ""

IMAGES=(
    "projex-suite-projex-api"
    "projex-suite-projex-web"
    "projex-suite-era-ai-api"
    "projex-suite-erabudget-api"
    "projex-suite-appcatalog-api"
    "projex-suite-wahub-gateway"
    "projex-suite-collab-server"
)

FAILED=0

for IMG in "${IMAGES[@]}"; do
    echo "=== $IMG ==="
    if docker image inspect "$IMG:latest" > /dev/null 2>&1; then
        trivy image --severity "$SEVERITY" "$IMG:latest" || FAILED=$((FAILED + 1))
    else
        echo "  Image not found, skipping"
    fi
    echo ""
done

if [ $FAILED -gt 0 ]; then
    echo "WARNING: $FAILED image(s) have vulnerabilities"
    exit 1
else
    echo "All images clean."
fi
