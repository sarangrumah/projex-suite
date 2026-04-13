# ProjeX Database Tables (32 total)

## Public Schema (shared, 5 tables)
- `tenants` — id, name, slug, domain, plan, branding, settings
- `plans` — id, name, price, features, limits
- `subscriptions` — tenant_id, plan_id, status, dates
- `billing` — tenant_id, invoice data, payment status
- `system_config` — key-value system settings

## Tenant Schema (per tenant, 26 tables)
### Core (10)
- `users` — accounts with encrypted PII
- `spaces` — project containers
- `work_items` — epics/stories/tasks/bugs
- `sprints` — sprint management
- `workflows` — visual workflow definitions
- `workflow_statuses` — status nodes
- `comments` — threaded comments
- `worklogs` — time entries
- `custom_field_definitions` — field registry
- `work_item_links` — dependencies

### Knowledge (2)
- `wiki_pages` — per-space docs
- `wiki_page_versions` — version history

### AppCatalog (4)
- `catalog_products` — product registry
- `catalog_documents` — BRD/FSD/TSD entities
- `catalog_doc_versions` — SemVerDoc history
- `catalog_repositories` — GitHub connections

### ERABudget (3)
- `budgets` — project budgets
- `budget_line_items` — cost breakdown
- `invoices` — invoice records

### Other (7)
- `goals` — OKR objectives
- `key_results` — OKR key results
- `automations` — automation rules
- `dashboards` — dashboard configs
- `dashboard_widgets` — widget instances
- `notifications` — notification queue
- `files` — attachment metadata

## Audit Schema (shared, 1 table)
- `audit.events` — immutable hash-chained log
