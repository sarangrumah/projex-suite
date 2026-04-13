# ProjeX Suite — Claude Code Execution Guide
## Phase 1: Foundation (8 Weeks)

**Target Server:** bct-production (202.74.75.40) Ubuntu 24.04
**Claude Code User:** bctadmin
**Date:** April 2026

---

## STEP 0: Prerequisites (One-time setup)

```bash
# SSH into BCT VPS
ssh bctadmin@202.74.75.40

# Verify Claude Code is installed
claude --version
# Should show v2.1.66 or later

# Verify Node.js 18+
node --version

# Verify Python 3.12+
python3 --version

# Verify Docker
docker --version
docker compose version

# Create project directory
mkdir -p ~/projex-suite
cd ~/projex-suite
git init

# Copy CLAUDE.md into project root
# (upload the CLAUDE.md file we generated)
```

---

## STEP 1: Project Scaffold (Day 1)

Open Claude Code in the project directory:

```bash
cd ~/projex-suite
claude
```

### Prompt 1.1: Initialize project structure

```
Create the full project directory structure for ProjeX Suite as defined in CLAUDE.md.

Create these files:
1. docker-compose.yml with all 18 services (use the exact spec from our TSD document)
2. docker-compose.dev.yml with development overrides (debug mode, volume mounts)
3. Caddyfile with reverse proxy routing for *.projex.id
4. backend/projex-api/requirements.txt with: fastapi, uvicorn, sqlalchemy[asyncio], alembic, asyncpg, pydantic[email], python-jose[cryptography], passlib[bcrypt], redis, celery, python-multipart, httpx
5. backend/projex-api/Dockerfile (Python 3.12-slim, non-root user, read-only FS)
6. frontend/projex-web/package.json with React 19 + TypeScript + Tailwind + Zustand + React Query + React Router
7. frontend/projex-web/Dockerfile (Node 22-alpine, multi-stage build)
8. .env.example with all required environment variables
9. .gitignore (Python + Node + Docker + IDE)

Use distroless/non-root containers. Include health checks in docker-compose.
```

### Prompt 1.2: Backend foundation

```
Create the FastAPI application foundation in backend/projex-api/app/:

1. main.py - FastAPI app with CORS, middleware stack, router includes, lifespan events
2. core/config.py - Pydantic Settings (DATABASE_URL, REDIS_URL, SECRET_KEY, JWT settings, etc.)
3. core/database.py - Async SQLAlchemy engine + session factory with schema-per-tenant support
4. core/security.py - JWT encode/decode (RS256), password hashing (bcrypt cost=12), AES-256 encryption for PII
5. core/deps.py - FastAPI dependencies (get_db, get_current_user, get_current_tenant)
6. middleware/tenant.py - Extract tenant from JWT + subdomain, set search_path per request
7. middleware/rate_limit.py - Redis-based rate limiter (1000/min standard, configurable)

Key requirements:
- All DB sessions MUST use async (asyncpg)
- Tenant middleware sets PostgreSQL search_path to tenant schema
- JWT payload includes: sub, tenant_id, role, permissions, device_fingerprint
- Config reads from environment variables (Vault-ready)
```

---

## STEP 2: Auth + Multi-Tenant (Week 1-2)

### Prompt 2.1: Database models

```
Create SQLAlchemy models in backend/projex-api/app/models/:

1. models/user.py - User model with:
   - id (UUID), email (VARCHAR, unique per tenant), email_encrypted (BYTEA)
   - password_hash, display_name, avatar_url
   - role (admin/member/viewer/guest), mfa_enabled, mfa_secret_encrypted
   - last_login_at, failed_login_count, locked_until
   - created_at, updated_at

2. models/tenant.py (in public schema, shared):
   - id (UUID), name, slug (unique), domain
   - plan (free/standard/premium/enterprise)
   - branding (JSONB: logo, colors, favicon)
   - settings (JSONB)
   - created_at, is_active

3. Create Alembic migration for initial schema:
   - Public schema: tenants table
   - Template tenant schema: users table
   - Function to create new tenant schema from template

Remember: email_encrypted uses AES-256-GCM via core/security.py encrypt_pii() function.
Write tests for the models in tests/test_models.py.
```

### Prompt 2.2: Auth endpoints

```
Create auth API in backend/projex-api/app/api/v1/auth.py:

Endpoints:
1. POST /api/v1/auth/register - Create account (validate email, hash password, create user)
2. POST /api/v1/auth/login - Login (email+password → JWT pair)
3. POST /api/v1/auth/refresh - Refresh access token
4. POST /api/v1/auth/mfa/setup - Enable MFA (generate TOTP secret, return QR URI)
5. POST /api/v1/auth/mfa/verify - Verify TOTP code
6. POST /api/v1/auth/logout - Invalidate refresh token
7. GET /api/v1/auth/me - Current user profile + permissions

Schemas in app/schemas/auth.py using Pydantic v2:
- LoginRequest, LoginResponse, RegisterRequest, TokenResponse, etc.

Security requirements:
- Password: bcrypt cost=12, min 12 chars, complexity validation
- JWT: RS256, access 15min, refresh 7days, includes device_fingerprint
- Login: 3 failed → CAPTCHA, 10 failed → lock 15min
- Response: never hint which field is wrong ("Email or password incorrect")

Write comprehensive tests in tests/test_auth.py (pytest + httpx AsyncClient).
Test: successful login, failed login, lockout, token refresh, MFA flow.
```

### Prompt 2.3: RBAC system

```
Create RBAC system in backend/projex-api/app/:

1. models/role.py - Role model with permissions JSONB
   Default roles: admin (all), member (standard), viewer (read-only), guest (limited)
   Custom roles: user-defined with granular permissions

2. Permission structure (define in core/permissions.py):
   - space:create, space:edit, space:delete, space:archive
   - item:create, item:edit, item:delete, item:assign
   - item:transition (workflow), item:comment
   - sprint:create, sprint:start, sprint:close
   - timesheet:log, timesheet:approve, timesheet:export
   - admin:users, admin:roles, admin:settings
   - field_security: { field_name: "visible" | "hidden" | "read_only" } per role

3. middleware/rbac.py - Decorator/dependency that checks permissions:
   @require_permission("item:create")
   async def create_item(...)

4. Field-level security middleware that filters response fields based on role

Write tests: admin can do everything, member can't delete spaces, guest can only read.
```

---

## STEP 3: Spaces + Work Items (Week 3-4)

### Prompt 3.1: Spaces

```
Create Spaces module:

1. models/space.py - Space model:
   id, name, key (unique, uppercase, 2-10 chars), description
   template (scrum/kanban/bug/blank), management_mode (company/team)
   settings (JSONB), nav_tabs (JSONB array), status (active/archived)
   created_by (FK users), created_at

2. api/v1/spaces.py - CRUD endpoints:
   POST /spaces - Create with template initialization
   GET /spaces - List (user has access)
   GET /spaces/{key} - Detail with settings
   PUT /spaces/{key} - Update
   DELETE /spaces/{key} - Archive (soft delete)

3. services/space_service.py - Business logic:
   - On create: auto-generate key from name (AIM from "PT AIM")
   - On create with template: create default workflow, issue types, board config
   - Template "scrum": workflow [To Do → In Progress → In Review → Done], types [Epic, Story, Task, Bug]
   - Template "kanban": workflow [Backlog → To Do → In Progress → Done], types [Task, Bug]

4. schemas/space.py - Pydantic models

Write tests: create space, duplicate key validation, template initialization, archive.
```

### Prompt 3.2: Work Items

```
Create Work Items module — this is the core entity:

1. models/work_item.py:
   id, space_id (FK), key (auto: AIM-101), sequence_num
   type (epic/story/task/bug/sub_task/cr), title (max 500)
   description (JSONB - TipTap format), status_id (FK workflow_statuses)
   priority (critical/high/normal/low), assignee_id, reporter_id
   parent_id (self-ref for hierarchy), sprint_id (FK)
   due_date, start_date, estimate_points, estimate_hours
   time_spent_seconds, labels (TEXT[]), custom_fields (JSONB)
   position (for ordering), created_at, updated_at
   Indexes: (space_id, status_id), (assignee_id), (sprint_id), (parent_id)

2. api/v1/items.py:
   POST /spaces/{key}/items - Create (with key auto-generation)
   GET /spaces/{key}/items - List with PQL filtering + pagination
   GET /items/{key} - Detail with relations
   PUT /items/{key} - Update (partial, auto-save friendly)
   DELETE /items/{key} - Soft delete (move to trash)
   POST /items/{key}/comments - Add comment
   POST /items/{key}/worklogs - Log work time

3. services/item_service.py:
   - Key generation: space.key + "-" + next sequence number
   - Parent-child validation (no circular refs)
   - Workflow transition validation (check allowed transitions)
   - Notify watchers on changes

4. models/comment.py and models/worklog.py

Write tests: create item, hierarchy, key auto-generation, workflow transition, 
link items, log work, pagination, PQL filtering.
```

---

## STEP 4: Kanban Board (Week 5-6)

### Prompt 4.1: Workflow Engine

```
Create Workflow Engine:

1. models/workflow.py:
   - workflows table: id, space_id, name, work_item_type, definition (JSONB), is_default
   - workflow_statuses table: id, workflow_id, name, category (todo/in_progress/done), color, position

2. Workflow definition JSONB format:
   {
     "statuses": ["todo-1", "inprog-1", "review-1", "done-1"],
     "transitions": [
       { "from": "todo-1", "to": "inprog-1", "conditions": [], "validators": [], "post_functions": [] },
       { "from": "inprog-1", "to": "review-1", "conditions": [{"type": "role", "roles": ["member", "admin"]}] },
       ...
     ]
   }

3. services/workflow_service.py:
   - validate_transition(item, target_status): check conditions + validators
   - execute_transition(item, target_status): run post-functions (assign, notify, webhook)
   - Create default workflows per template on Space creation

4. api/v1/workflows.py:
   GET /spaces/{key}/workflow - Get workflow with statuses
   PUT /workflows/{id} - Update workflow definition (admin only)
```

### Prompt 4.2: Board API + Frontend

```
Create Kanban Board backend + frontend:

BACKEND:
1. api/v1/board.py:
   GET /spaces/{key}/board - Returns board data:
   {
     "columns": [
       { "status": {...}, "items": [...], "wip_limit": 5, "count": 3 }
     ],
     "swimlanes": { "type": "none" | "epic" | "assignee" | "priority", "groups": [...] },
     "quick_filters": { "assignees": [...], "types": [...], "labels": [...] }
   }

   PUT /items/{key}/move - Move card:
   { "status_id": "uuid", "position": 3, "sprint_id": "uuid" }
   - Validates workflow transition
   - Updates position (reorder other items)
   - Triggers post-functions

FRONTEND (React):
2. Create frontend/projex-web/src/pages/BoardPage.tsx:
   - Kanban board with draggable columns (use @dnd-kit/core)
   - Card component with: key, title, assignee avatar, priority badge, SP estimate, timer icon
   - WIP limit display on column header (amber at limit, red over)
   - Swimlane toggle dropdown
   - Quick filter pills at top
   - Click card → open detail panel (right slide drawer)

3. Create reusable components:
   - components/Board/Column.tsx
   - components/Board/Card.tsx
   - components/Board/QuickFilters.tsx
   - components/Board/SwimlaneSwitcher.tsx
   - components/ItemDetail/DetailPanel.tsx (slide-in from right)

Use Zustand for board state, React Query for server data.
Implement optimistic updates for drag-drop (update UI immediately, sync to server).
```

---

## STEP 5: Docker + Security (Week 7-8)

### Prompt 5.1: Docker hardening

```
Finalize docker-compose.yml with full security hardening:

For EVERY service container, apply:
- user: "1000:1000" (non-root)
- read_only: true (with tmpfs for /tmp)
- security_opt: ["no-new-privileges:true"]
- cap_drop: ["ALL"]
- mem_limit and cpus set per service
- pids_limit: 100
- restart: unless-stopped

Network isolation:
- frontend: caddy, projex-web, projex-api
- backend (internal: true): all microservices
- db-net (internal: true): postgres, redis, meilisearch, minio, vault
- ai-net (internal: true): bima-ai-api, ollama
- monitoring (internal: true): prometheus, grafana

Caddy configuration:
- Auto-HTTPS with Let's Encrypt
- Wildcard cert for *.projex.id via Cloudflare DNS-01
- Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- Rate limiting: 1000 req/min per IP
- Reverse proxy routes to backend services

Create health check endpoints for every service.
```

### Prompt 5.2: Security baseline

```
Implement security baseline:

1. backend/projex-api/app/core/security.py - enhance with:
   - encrypt_pii(value) / decrypt_pii(value) using Fernet (key from Vault)
   - validate_password_strength(password) - min 12 chars, complexity
   - generate_device_fingerprint(request) - hash of user-agent + IP
   - sanitize_input(text) - strip XSS patterns from text inputs

2. middleware/security_headers.py:
   - Add all OWASP recommended headers to every response
   - CSP: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - Strict-Transport-Security: max-age=31536000; includeSubDomains

3. middleware/audit.py:
   - Log every CREATE, UPDATE, DELETE action
   - Include: actor_id, actor_ip, action, resource_type, resource_id, before/after state
   - Hash-chain: each entry's hash = SHA256(header + payload + prev_hash)
   - Write to audit schema (append-only, no DELETE permission)

4. Create comprehensive security tests:
   - SQL injection attempts (should all fail via ORM)
   - XSS in work item title/description
   - CSRF token validation
   - JWT expired token handling
   - Tenant isolation: User A cannot see User B's tenant data
   - Rate limiting: 1001st request returns 429
```

---

## STEP 6: Verification & Deploy (End of Week 8)

### Prompt 6.1: Integration tests

```
Create end-to-end integration tests in tests/test_e2e.py:

Test scenario E2E-01 (from our Test Strategy):
1. Register new user → verify account created
2. Login → verify JWT returned
3. Create Space "AIM" with Scrum template → verify default workflow created
4. Create Epic "Drone Project" → verify key AIM-1
5. Create Story under Epic → verify key AIM-2, parent_id set
6. Create Task under Story → verify AIM-3
7. View board → verify 3 items in "To Do" column
8. Drag AIM-3 to "In Progress" → verify status changed, workflow transition logged
9. Verify audit log has entries for all actions
10. Verify tenant isolation: create second tenant, verify no cross-access

Run with: pytest tests/test_e2e.py -x -v --tb=short
All tests must pass before Phase 1 is considered complete.
```

### Prompt 6.2: Deploy to VPS

```
Create deployment script deploy.sh that:

1. Pulls latest code from git
2. Builds Docker images with current git SHA as tag
3. Runs database migrations (alembic upgrade head)
4. Starts all services (docker compose up -d)
5. Waits for health checks to pass (curl /health on each service)
6. Runs smoke tests:
   - Can access login page
   - Can login with test account
   - Can create space
   - Can create work item
   - Board renders correctly
7. If any smoke test fails: rollback to previous image tag
8. Print deployment summary with service status

Also create:
- scripts/create-tenant.sh - Create new tenant with schema
- scripts/backup.sh - pg_dump + GPG encrypt + upload to MinIO
- scripts/restore.sh - Download from MinIO + decrypt + pg_restore
```

---

## Quick Reference: Claude Code Commands

```bash
# Start session
cd ~/projex-suite && claude

# Resume previous session
claude --resume

# Check project health
claude "/doctor"

# Compact context when session gets long
claude "/compact"

# Clear and start fresh
claude "/clear"
```

## Tips for Effective Claude Code Usage

1. **One feature per prompt** — Don't ask for auth + board + tests in one go
2. **Always verify** — After Claude writes code, run tests immediately
3. **Use TDD** — Ask Claude to write tests first, then implement
4. **Commit often** — `git commit` after each successful feature
5. **Compact when slow** — Use `/compact` when context gets too large
6. **Check CLAUDE.md** — Update it as architecture decisions are made
7. **Read the diff** — Always review what Claude changed before accepting

---

*Generated from ProjeX Suite initiation documents (13 docs, 130 BRs)*
*Ready for Phase 1 kickoff*