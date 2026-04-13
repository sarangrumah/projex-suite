---
name: docker-security
description: Docker security hardening patterns for ProjeX Suite. Use when creating Dockerfiles, docker-compose services, configuring networks, setting resource limits, or implementing container security. Covers rootless containers, network isolation, and Trivy scanning.
allowed-tools: Read, Write, Edit, Bash, Grep
---

# Docker Security Patterns

## Dockerfile Template (Python backend)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose Service Template

```yaml
service-name:
  build: ./backend/service-name
  user: "1000:1000"
  read_only: true
  tmpfs:
    - /tmp:size=100m
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  mem_limit: 512m
  cpus: 2.0
  pids_limit: 100
  restart: unless-stopped
  networks:
    - backend
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
    interval: 30s
    timeout: 5s
    retries: 3
```

## Network Isolation

```yaml
networks:
  frontend:          # External-facing via Caddy
    driver: bridge
  backend:           # Service-to-service only
    driver: bridge
    internal: true
  db-net:            # Database tier — NO external
    driver: bridge
    internal: true
  ai-net:            # AI inference — NO external
    driver: bridge
    internal: true
  wa-net:            # WhatsApp outbound only
    driver: bridge
  monitoring:        # Observability stack
    driver: bridge
    internal: true
```

Rule: `internal: true` means no outbound internet access. Only services on the same network can communicate.

## Resource Limits Per Service

| Service | Memory | CPU | PIDs |
|---------|--------|-----|------|
| caddy | 256m | 1.0 | 50 |
| projex-web | 256m | 1.0 | 50 |
| projex-api | 512m | 2.0 | 100 |
| projex-worker | 512m | 2.0 | 100 |
| postgres | 1g | 2.0 | 200 |
| redis | 256m | 0.5 | 50 |
| meilisearch | 512m | 1.0 | 50 |
| minio | 512m | 1.0 | 50 |
| era-ai-api | 512m | 2.0 | 100 |
| ollama | 12g | 4.0 | 200 |
| erabudget-api | 256m | 1.0 | 50 |
| appcatalog-api | 256m | 1.0 | 50 |
| vault | 256m | 0.5 | 50 |
| prometheus | 512m | 1.0 | 50 |

## Security Scanning

```bash
# Scan image for CVEs
trivy image projex-api:latest --severity HIGH,CRITICAL

# Scan in CI (fail on critical)
trivy image --exit-code 1 --severity CRITICAL projex-api:latest

# Scan docker-compose
trivy config docker-compose.yml
```

## CRITICAL RULES
- NEVER run containers as root — always `user: "1000:1000"`
- NEVER expose database ports to frontend network
- ALWAYS set `read_only: true` with tmpfs for /tmp
- ALWAYS set `cap_drop: ["ALL"]` and `no-new-privileges:true`
- ALWAYS include healthcheck on every service
- ALWAYS set memory and CPU limits
- ALWAYS use multi-stage builds to minimize image size
- NEVER store secrets in Dockerfiles or compose files — use Vault
