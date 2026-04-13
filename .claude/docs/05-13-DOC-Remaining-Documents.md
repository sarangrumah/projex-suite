# ══════════════════════════════════════════════════════════════
# DOC-SAB-001 — Solution Architecture Blueprint
# ══════════════════════════════════════════════════════════════
# ProjeX Suite v1.0 | April 13, 2026 | Ade Maryadi | DRAFT

## 1. Infrastructure Overview

### 1.1 Production Environment
- **Host:** Biznet Gio VPS (Ubuntu 24.04 LTS)
- **IP:** 202.74.75.40 (bct-production) or upgraded instance
- **Minimum Specs:** 8 vCPU, 16 GB RAM, 200 GB NVMe SSD
- **Recommended Specs:** 8 vCPU, 32 GB RAM, 200 GB NVMe SSD + GPU (for Ollama)
- **OS Hardening:** Unattended-upgrades, UFW firewall, fail2ban, SSH key-only

### 1.2 Staging Environment
- Separate VPS: 4 vCPU, 8 GB RAM, 100 GB SSD
- Uses qwen2.5:7b model (lighter) for cost efficiency
- Data anonymized from production snapshot (weekly)

### 1.3 Network Architecture
```
Internet → Cloudflare (DNS + DDoS) → VPS:443 → Caddy → Docker services
  - *.projex.id → Caddy wildcard cert
  - API: {tenant}.projex.id/api/v1/*
  - Web: {tenant}.projex.id/*
  - Portal: portal.{tenant}.projex.id/*
```

### 1.4 Docker Network Segmentation
| Network | Type | Purpose | Containers |
|---|---|---|---|
| frontend | bridge | External-facing via Caddy | caddy, projex-web, projex-api |
| backend | internal | Service-to-service | All microservices |
| db-net | internal | Database tier (no external) | postgres, redis, meilisearch, minio, vault |
| ai-net | internal | AI inference | era-ai-api, ollama |
| wa-net | bridge (outbound only) | WhatsApp API | wahub-gateway, wahub-worker |
| monitoring | internal | Observability | prometheus, grafana, loki |

### 1.5 SSL/TLS Configuration
- Caddy auto-provisions Let's Encrypt certificates
- Wildcard cert for *.projex.id via DNS-01 challenge (Cloudflare API)
- Internal mTLS between services via Caddy internal CA
- Minimum TLS 1.2, preferred TLS 1.3, HSTS enabled

### 1.6 Backup Strategy
| What | Frequency | Retention | Method | Storage |
|---|---|---|---|---|
| PostgreSQL (full) | Daily 2 AM WIB | 30 days | pg_dump + GPG encrypt | MinIO + offsite S3 |
| PostgreSQL (WAL) | Continuous | 7 days | pg_basebackup streaming | Local |
| MinIO files | Daily 3 AM | 14 days | mc mirror + encrypt | Offsite S3 |
| Docker volumes | Weekly | 4 weeks | tar + GPG | Offsite S3 |
| Vault secrets | On change | 90 days | Vault snapshot | Encrypted USB (offline) |

---

# ══════════════════════════════════════════════════════════════
# DOC-DD-001 — Data Dictionary & ERD
# ══════════════════════════════════════════════════════════════

## 1. Entity Relationship Summary

### 1.1 Core Entities (18 tables per tenant)
```
users ──1:N──▶ spaces (created_by)
users ──1:N──▶ work_items (assignee/reporter)
spaces ──1:N──▶ work_items
spaces ──1:N──▶ sprints
spaces ──1:N──▶ workflows ──1:N──▶ workflow_statuses
spaces ──1:N──▶ wiki_pages
work_items ──1:N──▶ work_items (parent/child)
work_items ──1:N──▶ worklogs
work_items ──1:N──▶ comments
work_items ──N:N──▶ work_items (links)
worklogs ──N:1──▶ users
sprints ──1:N──▶ work_items
```

### 1.2 AppCatalog Entities (5 tables per tenant)
```
catalog_products ──1:N──▶ catalog_documents
catalog_products ──1:N──▶ catalog_repositories
catalog_documents ──1:N──▶ catalog_doc_versions
```

### 1.3 ERABudget Entities (3 tables per tenant)
```
spaces ──1:1──▶ budgets
budgets ──1:N──▶ budget_line_items
spaces ──1:N──▶ invoices
```

### 1.4 Audit Entity (1 table, shared schema)
```
audit.events (append-only, hash-chained, cross-tenant)
```

### 1.5 Table Count Summary
| Schema | Tables | Description |
|---|---|---|
| public | 5 | tenants, plans, subscriptions, billing, system_config |
| tenant_{slug} | 26 | All business data (core + catalog + budget + wahub) |
| audit | 1 | Immutable audit events |
| **TOTAL per tenant** | **32** | |

### 1.6 Key Data Dictionary (Critical Fields)

| Table.Column | Type | Nullable | Encrypted | Masked | Description |
|---|---|---|---|---|---|
| users.email | VARCHAR(255) | NO | YES (AES-256) | YES (by role) | User email address |
| users.password_hash | VARCHAR(255) | NO | N/A (hashed) | N/A | bcrypt cost=12 |
| users.mfa_secret_encrypted | BYTEA | YES | YES | N/A | TOTP secret |
| work_items.title | VARCHAR(500) | NO | NO | NO | Work item title |
| work_items.description | JSONB | YES | NO | NO | TipTap rich text |
| work_items.custom_fields | JSONB | YES | Selective | Selective | Per field-level security |
| worklogs.seconds_spent | INT | NO | NO | NO | Time in seconds |
| catalog_doc_versions.content | JSONB | NO | NO | NO | Full document content |
| catalog_doc_versions.prev_version_hash | VARCHAR(64) | YES | NO | NO | Hash chain link |
| audit.events.entry_hash | VARCHAR(64) | NO | NO | NO | SHA-256 tamper detection |
| invoices.client_npwp | VARCHAR(20) | YES | YES | YES | Indonesian tax ID |
| budgets.total_amount | DECIMAL(15,2) | NO | NO | YES (viewer role) | Budget amount |

---

# ══════════════════════════════════════════════════════════════
# DOC-API-001 — API Specification
# ══════════════════════════════════════════════════════════════

## 1. API Overview
- **Base URL:** `https://{tenant}.projex.id/api/v1`
- **Auth:** Bearer JWT (RS256) — `Authorization: Bearer {token}`
- **Format:** JSON (request + response)
- **Versioning:** URL path (`/v1/`)
- **Rate Limits:** Standard: 1000/min, Premium: 5000/min, Enterprise: Unlimited
- **Pagination:** `?page=1&per_page=50` (max 200)
- **Filtering:** PQL query string: `?pql=status="In Progress" AND assignee=currentUser()`
- **Sorting:** `?sort=created_at:desc`

## 2. Endpoint Inventory

| Method | Endpoint | Module | Description |
|---|---|---|---|
| POST | /auth/login | Auth | Login, returns JWT |
| POST | /auth/refresh | Auth | Refresh token |
| POST | /auth/mfa/verify | Auth | Verify TOTP |
| GET | /me | Auth | Current user profile |
| POST | /spaces | Spaces | Create space |
| GET | /spaces | Spaces | List spaces |
| GET | /spaces/{key} | Spaces | Get space |
| PUT | /spaces/{key} | Spaces | Update space |
| POST | /spaces/{key}/items | Work Items | Create item |
| GET | /spaces/{key}/items | Work Items | List/filter items |
| GET | /items/{key} | Work Items | Get item detail |
| PUT | /items/{key} | Work Items | Update item |
| POST | /items/{key}/comments | Comments | Add comment |
| POST | /items/{key}/worklogs | Worklogs | Log work |
| PUT | /items/{key}/move | Board | Move card |
| GET | /spaces/{key}/board | Board | Board data |
| POST | /spaces/{key}/sprints | Sprints | Create sprint |
| POST | /sprints/{id}/start | Sprints | Start sprint |
| POST | /sprints/{id}/close | Sprints | Close sprint |
| GET | /sprints/{id}/burndown | Reports | Burndown data |
| GET | /sprints/{id}/velocity | Reports | Velocity data |
| GET | /timesheet | Timesheet | Weekly grid |
| POST | /timesheet/entries | Timesheet | Log entries |
| POST | /timesheet/submit | Timesheet | Submit approval |
| POST | /timesheet/{id}/approve | Timesheet | Approve |
| POST | /ai/chat | ERA AI | Chat message |
| POST | /ai/query | ERA AI | Text-to-SQL |
| GET | /ai/suggestions | ERA AI | Proactive alerts |
| POST | /catalog/products | AppCatalog | Register product |
| GET | /catalog/products | AppCatalog | List products |
| POST | /catalog/documents | AppCatalog | Create document |
| GET | /catalog/documents/{id}/versions | AppCatalog | Version history |
| POST | /catalog/webhooks/github | AppCatalog | GitHub webhook |
| POST | /budgets | ERABudget | Create budget |
| GET | /budgets/{id}/report | ERABudget | Budget report |
| POST | /invoices | ERABudget | Generate invoice |
| POST | /wahub/send | WA-Hub | Send message |
| POST | /wahub/templates | WA-Hub | Create template |
| GET | /dashboards/{id} | Dashboards | Dashboard data |
| GET | /goals | Goals | List goals/OKRs |
| **TOTAL: 40 endpoints** | | | |

---

# ══════════════════════════════════════════════════════════════
# DOC-SAD-001 — Security Architecture Document
# ══════════════════════════════════════════════════════════════

## 1. Threat Model (STRIDE)

| Threat | Category | Target | Mitigation |
|---|---|---|---|
| T1 | Spoofing | Authentication | MFA, JWT with device fingerprint, SSO |
| T2 | Tampering | Data integrity | Hash-chained audit log, input validation |
| T3 | Repudiation | Actions | Immutable audit trail, digital signatures |
| T4 | Information Disclosure | Data leakage | AES-256 encryption, data masking, TLS 1.3 |
| T5 | Denial of Service | Availability | Rate limiting, resource limits, WAF |
| T6 | Elevation of Privilege | Authorization | RBAC, tenant isolation, no-new-privileges |

## 2. Security Controls Matrix

| Control | Implementation | Layer |
|---|---|---|
| WAF | Caddy + OWASP CRS | Network |
| DDoS Protection | Cloudflare | Network |
| TLS 1.3 | Caddy auto-HTTPS | Transport |
| Internal mTLS | Caddy internal CA | Transport |
| JWT Auth (RS256) | Custom + Keycloak | Application |
| MFA (TOTP) | pyotp library | Application |
| RBAC | Custom middleware | Application |
| Input Validation | Pydantic v2 | Application |
| SQL Injection Prevention | SQLAlchemy ORM | Application |
| XSS Prevention | DOMPurify + CSP | Application |
| CSRF Prevention | SameSite cookies + CSRF tokens | Application |
| Brute Force | Rate limit + lockout + CAPTCHA | Application |
| Data Encryption (rest) | pgcrypto AES-256-GCM | Data |
| Data Masking | Dynamic per-role middleware | Data |
| Secret Management | HashiCorp Vault | Infrastructure |
| Container Hardening | Rootless + read-only + cap_drop ALL | Infrastructure |
| Image Scanning | Trivy in CI/CD | CI/CD |
| Runtime Monitoring | Falco | Runtime |
| Audit Logging | Hash-chained append-only | Compliance |

## 3. Compliance Alignment

| Standard | Applicability | ProjeX Coverage |
|---|---|---|
| UU PDP (Indonesian Data Protection) | All tenants | Data in Indonesia, consent management, right to delete |
| OWASP Top 10 (2021) | All | A01-A10 addressed in security controls |
| SOC 2 Type II | Enterprise tenants | Audit trail, access controls, encryption (target) |
| ISO 27001 | Enterprise tenants | Event logging, access control, incident response (target) |

---

# ══════════════════════════════════════════════════════════════
# DOC-TS-001 — Test Strategy Document
# ══════════════════════════════════════════════════════════════

## 1. Test Levels

| Level | Scope | Tools | Coverage Target |
|---|---|---|---|
| Unit Tests | Functions, models, utilities | pytest, vitest | 80% code coverage |
| Integration Tests | API endpoints, DB queries | pytest + httpx | 100% of API endpoints |
| Component Tests | React components | React Testing Library | Critical user flows |
| E2E Tests | Full user journeys | Playwright | 20 critical scenarios |
| Security Tests | Vulnerability scanning | Trivy, OWASP ZAP, custom | Zero critical/high |
| Performance Tests | Load testing | Locust | p95 < 500ms at 100 concurrent |
| AI Tests | ERA AI responses | Custom eval framework | 80% accuracy on worklog parsing |

## 2. Critical Test Scenarios (E2E)

| # | Scenario | Modules Covered |
|---|---|---|
| E2E-01 | Register → Login → Create Space → Create Items → Board drag-drop | Auth, Spaces, Items, Board |
| E2E-02 | Sprint create → Planning → Start → Burndown → Close | Sprints, Reports |
| E2E-03 | Timesheet: Timer → Quick log → Submit → Approve | Timesheet |
| E2E-04 | AI: "Log 2h intercompany" → Confirm → Verify worklog created | ERA AI, Timesheet |
| E2E-05 | AppCatalog: Create product → Create BRD → Edit → Version history | AppCatalog |
| E2E-06 | GitHub webhook → AI doc update → PO review → Approve | AppCatalog, ERA AI |
| E2E-07 | Budget create → Timesheet → Invoice generate → e-Faktur | ERABudget |
| E2E-08 | WA-Hub: Sprint alert trigger → WA message delivered | WA-Hub |
| E2E-09 | Multi-tenant: Tenant A cannot see Tenant B data | Security |
| E2E-10 | Brute force: 10 failed logins → account lockout → CAPTCHA | Security |

## 3. CI/CD Pipeline Test Gates

```
Push → Lint → Unit Tests → Build → Trivy Scan → Integration Tests
  → IF critical vuln: BLOCK deployment
  → IF tests pass: Deploy to staging
  → E2E Tests on staging
  → IF pass: Manual approval gate → Deploy to production
```

---

# ══════════════════════════════════════════════════════════════
# DOC-DP-001 — Deployment Plan
# ══════════════════════════════════════════════════════════════

## 1. Deployment Strategy
- **Method:** Rolling deployment via Docker Compose
- **Zero-downtime:** Blue-green with Caddy upstream switching
- **Rollback:** Previous image tags retained; `docker compose up -d` with previous version

## 2. Deployment Procedure

```
1. Developer pushes to main branch
2. GitHub Actions triggers:
   a. Run linter (ruff for Python, ESLint for React)
   b. Run unit + integration tests
   c. Build Docker images with commit SHA tag
   d. Trivy scan on built images
   e. Push to private registry (GitHub Container Registry)
3. Manual approval gate (for production)
4. SSH into VPS, run deployment script:
   a. Pull new images
   b. Run database migrations (Alembic)
   c. docker compose up -d (rolling restart)
   d. Health check verification (curl /health)
   e. Smoke test (automated)
5. IF smoke test fails: automatic rollback to previous tag
```

## 3. Environment Configuration

| Variable | Dev | Staging | Production |
|---|---|---|---|
| DATABASE_URL | localhost:5432/projex_dev | staging-db:5432/projex | vault://db/creds |
| OLLAMA_MODEL | qwen2.5:7b | qwen2.5:7b | qwen2.5:14b |
| LOG_LEVEL | DEBUG | INFO | WARNING |
| CORS_ORIGINS | http://localhost:3000 | https://staging.projex.id | https://*.projex.id |
| RATE_LIMIT | 10000/min | 5000/min | 1000/min (standard) |

## 4. Monitoring & Alerting

| Metric | Threshold | Alert Channel |
|---|---|---|
| API response time p95 | > 500ms for 5 min | Slack + WA |
| Error rate (5xx) | > 1% for 2 min | Slack + WA + Email |
| CPU usage | > 80% for 10 min | Slack |
| Memory usage | > 85% for 5 min | Slack + WA |
| Disk usage | > 80% | Email |
| SSL cert expiry | < 14 days | Email |
| Container restart | > 3 in 10 min | Slack + WA |

---

# ══════════════════════════════════════════════════════════════
# DOC-PP-001 — Project Plan
# ══════════════════════════════════════════════════════════════

## 1. Timeline Summary

| Phase | Start | End | Duration | Team | Dependencies |
|---|---|---|---|---|---|
| 1. Foundation | Apr 21, 2026 | Jun 13, 2026 | 8 weeks | Ade + 1 contract | None |
| 2. Agile Core | Jun 16 | Jul 25 | 6 weeks | Ade + 1 contract | Phase 1 |
| 3. Timesheet | Jul 28 | Aug 21 | 4 weeks | Ade | Phase 1 |
| 4. ERA AI | Aug 24 | Sep 18 | 4 weeks | Ade | Phase 1 + Ollama setup |
| 5. Views | Sep 21 | Oct 16 | 4 weeks | Ade + 1 frontend | Phase 2 |
| 6. Dashboards | Oct 19 | Nov 6 | 3 weeks | Ade | Phase 2 + 3 |
| 7. Docs/Wiki | Nov 9 | Nov 27 | 3 weeks | Ade | Phase 1 |
| 8. AppCatalog | Dec 1 | Jan 2, 2027 | 5 weeks | Ade + 1 contract | Phase 4 + 7 |
| 9. ERABudget | Jan 5 | Jan 30 | 4 weeks | Ade | Phase 3 |
| 10. WA-Hub | Feb 2 | Feb 20 | 3 weeks | Ade | Existing wahub codebase |
| 11. SaaS | Feb 23 | Mar 20 | 4 weeks | Ade + 1 contract | Phase 1-10 |

## 2. Resource Allocation

| Role | Phase 1-4 | Phase 5-8 | Phase 9-11 |
|---|---|---|---|
| Lead Engineer (Ade) | 100% | 100% | 100% |
| Contract Backend Dev | 50% | 0% | 50% |
| Contract Frontend Dev | 0% | 50% | 0% |
| QA (automated) | 20% | 30% | 30% |

## 3. Key Milestones

| Date | Milestone | Gate Criteria |
|---|---|---|
| Jun 13, 2026 | Phase 1 Complete | Auth + Board + Docker working |
| Sep 18, 2026 | **MVP LAUNCH** | Phase 1-4, 3 internal users |
| Jan 2, 2027 | **BETA LAUNCH** | Phase 1-8, 3 pilot tenants |
| Mar 20, 2027 | **GA LAUNCH** | Phase 1-11, public availability |

---

# ══════════════════════════════════════════════════════════════
# DOC-RR-001 — Risk Register
# ══════════════════════════════════════════════════════════════

| ID | Risk | Category | Probability | Impact | Score | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| R01 | Scope creep from 45 modules | Scope | High (4) | High (4) | 16 | Strict MVP scope; Phase 1-4 only for MVP; defer non-critical | Ade | Active |
| R02 | Single developer bottleneck | Resource | High (4) | High (4) | 16 | Claude Code acceleration; hire 1-2 contractors Phase 5+ | Ade | Active |
| R03 | Ollama performance insufficient on VPS | Technical | Medium (3) | Medium (3) | 9 | Start qwen2.5:7b; benchmark; upgrade to 14b/GPU when needed | Ade | Active |
| R04 | Market adoption resistance | Business | Medium (3) | High (4) | 12 | Generous free tier; Jira import tool; pilot with existing BCT clients | Ade | Active |
| R05 | Security vulnerability in production | Security | Low (2) | Critical (5) | 10 | Security-by-design; Trivy CI scan; OWASP ZAP; pentest before launch | Ade | Active |
| R06 | Multi-tenant data isolation breach | Security | Low (2) | Critical (5) | 10 | Schema-per-tenant; tenant_id in every query; middleware enforcement; pentest | Ade | Active |
| R07 | GitHub API rate limits for AppCatalog | Technical | Medium (3) | Low (2) | 6 | GitHub App (higher limits); webhook not polling; aggressive caching | Ade | Monitoring |
| R08 | VPS provider outage | Infrastructure | Low (2) | High (4) | 8 | Daily backups to offsite S3; documented recovery procedure; 4h RTO target | Ade | Active |
| R09 | AI hallucination in doc updates | Technical | Medium (3) | Medium (3) | 9 | All AI outputs require human review; PATCH auto-apply only; MINOR/MAJOR need PO approval | Ade | Active |
| R10 | Dependency vulnerability (CVE) | Security | Medium (3) | Medium (3) | 9 | Dependabot enabled; Trivy daily scan; automated PR for updates | Ade | Active |
| R11 | Competitor launches similar product | Business | Low (2) | Medium (3) | 6 | Speed to market; unique AppCatalog+AI combo; Indonesian localization moat | Ade | Monitoring |
| R12 | Indonesian regulation change (UU PDP) | Compliance | Low (2) | Medium (3) | 6 | Self-hosted option ensures compliance; monitor regulation updates | Ade | Monitoring |

**Scoring:** Probability (1-5) × Impact (1-5) = Risk Score. Critical: ≥15, High: 10-14, Medium: 6-9, Low: 1-5

---

# ══════════════════════════════════════════════════════════════
# DOC-RTM-001 — Requirements Traceability Matrix
# ══════════════════════════════════════════════════════════════

## 1. Traceability: BRD → FSD → TSD → Test

| BRD Req | FSD Use Case | TSD Component | DB Table | API Endpoint | Test Case |
|---|---|---|---|---|---|
| BR-001 (Create Space) | UC-002 | spaces table | spaces | POST /spaces | E2E-01 |
| BR-007 (Work Items hierarchy) | UC-003, UC-004 | work_items table | work_items | POST /spaces/{key}/items | E2E-01 |
| BR-016 (Custom Fields) | UC-004 (edit) | custom_field_definitions | custom_field_definitions | PUT /items/{key} | Unit-CF-01 |
| BR-021 (Kanban Board) | UC-005 | work_items + statuses | work_items, workflow_statuses | GET /spaces/{key}/board | E2E-01 |
| BR-028 (Backlog) | UC-006 | work_items (sprint_id=null) | work_items | GET /spaces/{key}/items?sprint=backlog | E2E-02 |
| BR-033 (Sprints) | UC-007 | sprints table | sprints | POST /spaces/{key}/sprints | E2E-02 |
| BR-038 (Workflows) | UC-008 | workflows + statuses | workflows, workflow_statuses | PUT /workflows/{id} | Unit-WF-01 |
| BR-043 (PQL Search) | UC-009 | PQL parser → SQL | work_items | GET /spaces/{key}/items?pql= | Unit-PQL-01 |
| BR-071 (Timesheet Grid) | UC-010 | worklogs table | worklogs | GET /timesheet | E2E-03 |
| BR-074 (Timesheet Approval) | UC-011 | worklogs.approval_status | worklogs | POST /timesheet/approve | E2E-03 |
| BR-098 (AI Worklog) | UC-015 | era-ai-api + Ollama | worklogs | POST /ai/chat | E2E-04 |
| BR-104 (AI Doc Update) | UC-017 | appcatalog-worker + AI | catalog_doc_versions | POST /catalog/webhooks/github | E2E-06 |
| BR-108 (Budget) | UC-018 | budgets table | budgets | POST /budgets | E2E-07 |
| BR-111 (Invoice) | UC-019 | invoices table | invoices | POST /invoices | E2E-07 |
| BR-116 (WA Sprint Alert) | UC-020 | wahub-gateway | wahub_messages | POST /wahub/send | E2E-08 |
| BR-122 (AppCatalog Product) | UC-020 | catalog_products | catalog_products | POST /catalog/products | E2E-05 |
| BR-123 (Doc Versioning) | UC-021 | catalog_doc_versions | catalog_doc_versions | GET /catalog/documents/{id}/versions | E2E-05 |
| NFR-008 (Encryption) | — | pgcrypto + Fernet | users.email_encrypted | — | Security-01 |
| NFR-010 (SQLi Prevention) | — | SQLAlchemy ORM | — | All endpoints | Security-02 |
| NFR-024 (Tenant Isolation) | WF-001 | Schema-per-tenant | all tables | All endpoints | E2E-09 |

## 2. Coverage Summary

| Source | Total Items | Traced | Coverage |
|---|---|---|---|
| Business Requirements (BR) | 130 | 130 | 100% |
| Non-Functional Requirements (NFR) | 25 | 25 | 100% |
| Business Rules (BZ) | 15 | 15 | 100% |
| Use Cases (UC) | 21 | 21 | 100% |
| API Endpoints | 40 | 40 | 100% |
| E2E Test Scenarios | 10 | 10 | 100% |
| Database Tables | 32 | 32 | 100% |

---

*ALL DOCUMENTS COMPLETE*
*Document Set: 13 of 13*
*Total Business Requirements: 130*
*Total NFRs: 25*
*Total Business Rules: 15*
*Total Use Cases: 21*
*Total API Endpoints: 40*
*Total Database Tables: 32*
*Total E2E Test Scenarios: 10*
*Total Docker Services: 18*
*Total Risk Items: 12*
