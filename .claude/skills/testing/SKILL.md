---
name: testing
description: Testing patterns for ProjeX Suite. Use when writing unit tests (pytest/vitest), integration tests (httpx), E2E tests (Playwright), or security tests. Covers TDD workflow, fixtures, factories, and multi-tenant test isolation.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Testing Patterns

## Pytest Backend Template

```python
# tests/test_{module}.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from tests.conftest import get_auth_headers, create_test_tenant

@pytest.mark.asyncio
async def test_create_{module}():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await get_auth_headers(client, role="admin")
        response = await client.post(
            "/api/v1/{module}s",
            json={"name": "Test Item"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == "Test Item"
        assert "errors" in data and data["errors"] == []

@pytest.mark.asyncio
async def test_create_{module}_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/{module}s", json={"name": "Test"})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_tenant_isolation():
    """Tenant A cannot see Tenant B data."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers_a = await get_auth_headers(client, tenant="tenant_a")
        headers_b = await get_auth_headers(client, tenant="tenant_b")
        
        # Create in tenant A
        await client.post("/api/v1/{module}s", json={"name": "A Item"}, headers=headers_a)
        
        # List from tenant B should not see A's data
        resp = await client.get("/api/v1/{module}s", headers=headers_b)
        items = resp.json()["data"]
        assert all(item["name"] != "A Item" for item in items)
```

## Test Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from app.core.security import create_access_token

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

async def get_auth_headers(client, role="member", tenant="tenant_test"):
    """Register + login, return auth headers."""
    token = create_access_token(
        data={"sub": "test-user-id", "tenant_id": tenant, "role": role,
              "permissions": ["item:create", "item:edit", "space:create"]}
    )
    return {"Authorization": f"Bearer {token}"}
```

## Vitest Frontend Template

```tsx
// src/components/__tests__/{Component}.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { {Component} } from "../{Component}";

describe("{Component}", () => {
  it("renders title", () => {
    render(<{Component} title="Test" />);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  it("calls onAction when clicked", () => {
    const onAction = vi.fn();
    render(<{Component} title="Test" onAction={onAction} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onAction).toHaveBeenCalledOnce();
  });
});
```

## TDD Workflow
1. Write failing test first
2. Run: `pytest tests/test_{module}.py::test_name -x -v`
3. Implement minimum code to pass
4. Run test again — should pass
5. Refactor
6. Run full suite: `pytest -x -v`

## CRITICAL RULES
- ALWAYS write tests BEFORE implementation (TDD)
- ALWAYS test tenant isolation for new endpoints
- ALWAYS test RBAC: admin can, member limited, guest read-only
- ALWAYS test validation: missing fields, invalid types, boundary values
- ALWAYS test auth: expired token, wrong tenant, missing header
- NEVER mock the database in integration tests — use real async DB
- ALWAYS run `pytest -x` (stop on first failure) during development
