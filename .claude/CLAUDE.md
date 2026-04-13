# ProjeX Suite

## Project Overview
ProjeX Suite is a full Jira Software replacement + ClickUp best features + unique AI/AppCatalog/Budget/WhatsApp capabilities. SaaS multi-tenant platform for Indonesian SME software teams.

**Stack**: FastAPI (Python 3.12) + React 19 + TypeScript + Tailwind + PostgreSQL 16 + Redis 7 + Docker
**Architecture**: 6 microservices, 18 Docker containers, schema-per-tenant

## Key Directories
```
projex-suite/
├── .claude/
│   ├── CLAUDE.md             # This file (project instructions)
│   ├── settings.json         # Permissions & env config
│   ├── agents/               # Custom agents (architect, code-reviewer, security-auditor)
│   ├── skills/               # Custom skills (fastapi, react, testing, etc.)
│   └── docs/                 # 13 initiation documents + references
├── docker-compose.yml        # All 18 services
├── docker-compose.dev.yml    # Dev overrides
├── Caddyfile                 # Reverse proxy config
├── backend/
│   ├── projex-api/           # FastAPI main gateway (port 8000)
│   │   ├── app/
│   │   │   ├── main.py       # FastAPI app entry
│   │   │   ├── core/         # Config, security, db, deps
│   │   │   ├── models/       # SQLAlchemy models
│   │   │   ├── schemas/      # Pydantic v2 schemas
│   │   │   ├── api/v1/       # Route handlers
│   │   │   ├── services/     # Business logic
│   │   │   └── middleware/    # Tenant, auth, rate limit
│   │   ├── alembic/          # DB migrations
│   │   ├── tests/            # pytest
│   │   └── Dockerfile
│   ├── era-ai-api/          # AI microservice (port 8100)
│   ├── erabudget-api/        # Budget microservice (port 8200)
│   ├── appcatalog-api/       # AppCatalog microservice (port 8300)
│   ├── collab-server/        # Yjs WebSocket (port 8400)
│   └── wahub-gateway/        # WA-Hub (port 8500)
├── frontend/
│   ├── projex-web/           # React 19 SPA
│   │   ├── src/
│   │   │   ├── components/   # Reusable UI components
│   │   │   ├── pages/        # Route pages
│   │   │   ├── hooks/        # Custom React hooks
│   │   │   ├── stores/       # Zustand stores
│   │   │   ├── services/     # API client (axios/fetch)
│   │   │   └── types/        # TypeScript interfaces
│   │   └── Dockerfile
│   └── client-portal/        # White-label portal (later)
├── shared/
│   ├── db-schemas/           # Shared SQL schemas
│   └── proto/                # Shared types/interfaces
└── docs/                     # Project documentation
    └── *.docx                # 13 initiation documents
```

## Commands
- **Backend**: `cd backend/projex-api && uvicorn app.main:app --reload --port 8000`
- **Frontend**: `cd frontend/projex-web && npm run dev`
- **Tests**: `cd backend/projex-api && pytest -x -v`
- **Lint**: `ruff check backend/ --fix` and `cd frontend/projex-web && npx eslint src/`
- **Migration**: `cd backend/projex-api && alembic upgrade head`
- **Docker**: `docker compose up -d`
- **Type check**: `cd frontend/projex-web && npx tsc --noEmit`

## Code Style
- Python: ruff formatter, strict typing, docstrings on public functions
- TypeScript: strict mode, prefer interfaces over types, no `any`
- SQL: SQLAlchemy ORM ONLY — never raw SQL (security requirement)
- API: FastAPI with Pydantic v2, auto-OpenAPI docs
- React: functional components + hooks, Zustand for state, React Query for server state

## Architecture Rules
- EVERY database query MUST include tenant_id filter (middleware enforces)
- EVERY API endpoint returns `{ data, meta, errors }` envelope
- EVERY password hashed with bcrypt cost=12
- EVERY PII field (email, phone, NPWP) encrypted with AES-256 before DB storage
- JWT access tokens: 15 min TTL, refresh: 7 days with rotation
- AI-generated SQL: SELECT only, validated against whitelist patterns

## Current Phase: Phase 1 — Foundation (8 weeks)
Deliverables:
1. Auth (register/login/MFA/JWT/refresh) with multi-tenant support
2. RBAC (Admin/Member/Viewer/Guest + custom roles + field-level security)
3. Multi-tenant middleware (schema-per-tenant, tenant_id enforcement)
4. Spaces (CRUD with templates: Scrum/Kanban/Bug/Blank)
5. Work Items (Epic/Story/Task/Bug/Sub-task + custom types)
6. Custom Fields (all types including Formula and Rollup)
7. Kanban Board (drag-drop, WIP limits, swimlanes, quick filters)
8. Docker Compose (all 18 services with network isolation)
9. Security baseline (TLS, encryption, headers, rate limiting)

## Testing
- Run single test: `pytest tests/test_auth.py -x -v`
- Run with coverage: `pytest --cov=app --cov-report=term-missing`
- Frontend: `cd frontend/projex-web && npx vitest run`
- Always write tests for new API endpoints before implementation (TDD)