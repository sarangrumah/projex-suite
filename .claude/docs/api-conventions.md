# ProjeX API Conventions

## Response Envelope
Every endpoint returns: `{ "data": ..., "meta": { "page", "per_page", "total" }, "errors": [] }`

## HTTP Status Codes
- 200: Success (GET, PUT)
- 201: Created (POST)
- 204: No Content (DELETE)
- 400: Validation error
- 401: Authentication required
- 403: Permission denied (RBAC)
- 404: Not found (or wrong tenant)
- 409: Conflict (concurrent edit)
- 422: Business rule violation
- 429: Rate limited

## URL Patterns
- `POST /api/v1/{resource}s` — Create
- `GET /api/v1/{resource}s` — List (paginated)
- `GET /api/v1/{resource}s/{id}` — Detail
- `PUT /api/v1/{resource}s/{id}` — Update (partial)
- `DELETE /api/v1/{resource}s/{id}` — Soft delete

## Pagination
`?page=1&per_page=50` (max 200)

## Filtering
PQL: `?pql=status="In Progress" AND assignee=currentUser()`

## Sorting
`?sort=created_at:desc,priority:asc`
