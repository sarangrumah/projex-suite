"""Space endpoint tests: CRUD, template initialization, key generation, archive."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.core.permissions import ALL_PERMISSIONS
from app.main import app

BASE_URL = "http://test"


def _admin_headers(tenant: str = "test-tenant") -> dict[str, str]:
    token = create_access_token({
        "sub": "admin-user-id",
        "tenant_id": tenant,
        "role": "admin",
        "permissions": ALL_PERMISSIONS,
    })
    return {"Authorization": f"Bearer {token}"}


def _viewer_headers(tenant: str = "test-tenant") -> dict[str, str]:
    token = create_access_token({
        "sub": "viewer-user-id",
        "tenant_id": tenant,
        "role": "viewer",
        "permissions": ["item:comment", "budget:view"],
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as ac:
        yield ac


# ── Create ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_space_scrum(client: AsyncClient):
    response = await client.post(
        "/api/v1/spaces/",
        json={"name": "Drone Project", "key": "AIM", "template": "scrum"},
        headers=_admin_headers(),
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["key"] == "AIM"
    assert data["template"] == "scrum"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_space_auto_key(client: AsyncClient):
    response = await client.post(
        "/api/v1/spaces/",
        json={"name": "PT AIM Indonesia", "template": "kanban"},
        headers=_admin_headers(),
    )
    assert response.status_code == 201
    key = response.json()["data"]["key"]
    assert key.isalpha() and key.isupper()


@pytest.mark.asyncio
async def test_create_space_duplicate_key(client: AsyncClient):
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/",
        json={"name": "Alpha", "key": "DUPE", "template": "blank"},
        headers=headers,
    )
    response = await client.post(
        "/api/v1/spaces/",
        json={"name": "Beta", "key": "DUPE", "template": "blank"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_space_viewer_forbidden(client: AsyncClient):
    response = await client.post(
        "/api/v1/spaces/",
        json={"name": "Forbidden", "key": "NOPE", "template": "blank"},
        headers=_viewer_headers(),
    )
    assert response.status_code == 403


# ── List ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_spaces(client: AsyncClient):
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/",
        json={"name": "List Space", "key": "LS", "template": "blank"},
        headers=headers,
    )
    response = await client.get("/api/v1/spaces/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 1
    assert isinstance(data["data"], list)


# ── Get ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_space(client: AsyncClient):
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/",
        json={"name": "Get Space", "key": "GS", "template": "scrum"},
        headers=headers,
    )
    response = await client.get("/api/v1/spaces/GS", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["key"] == "GS"
    assert "nav_tabs" in data


@pytest.mark.asyncio
async def test_get_space_not_found(client: AsyncClient):
    response = await client.get("/api/v1/spaces/NOPE", headers=_admin_headers())
    assert response.status_code == 404


# ── Update ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_space(client: AsyncClient):
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/",
        json={"name": "Update Space", "key": "US", "template": "blank"},
        headers=headers,
    )
    response = await client.put(
        "/api/v1/spaces/US",
        json={"name": "Updated Space", "description": "New description"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Space"


# ── Archive ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_archive_space(client: AsyncClient):
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/",
        json={"name": "Archive Space", "key": "AS", "template": "blank"},
        headers=headers,
    )
    response = await client.delete("/api/v1/spaces/AS", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "archived"


# ── No auth ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_spaces_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/spaces/")
    assert response.status_code in (401, 403)
