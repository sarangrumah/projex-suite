"""Work Item endpoint tests: CRUD, key generation, hierarchy, comments, worklogs."""

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


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as ac:
        yield ac


async def _create_space(client: AsyncClient, key: str = "TST") -> dict:
    """Helper: create a space and return response data."""
    resp = await client.post(
        "/api/v1/spaces/",
        json={"name": "Test Space", "key": key, "template": "scrum"},
        headers=_admin_headers(),
    )
    return resp.json()["data"]


# ── Create items ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    await _create_space(client, "CI")
    response = await client.post(
        "/api/v1/spaces/CI/items",
        json={"title": "First Task", "type": "task"},
        headers=_admin_headers(),
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["key"] == "CI-1"
    assert data["type"] == "task"
    assert data["title"] == "First Task"


@pytest.mark.asyncio
async def test_create_item_auto_key_sequence(client: AsyncClient):
    await _create_space(client, "SEQ")
    headers = _admin_headers()
    r1 = await client.post(
        "/api/v1/spaces/SEQ/items",
        json={"title": "Epic One", "type": "epic"},
        headers=headers,
    )
    r2 = await client.post(
        "/api/v1/spaces/SEQ/items",
        json={"title": "Story One", "type": "story"},
        headers=headers,
    )
    r3 = await client.post(
        "/api/v1/spaces/SEQ/items",
        json={"title": "Task One", "type": "task"},
        headers=headers,
    )
    assert r1.json()["data"]["key"] == "SEQ-1"
    assert r2.json()["data"]["key"] == "SEQ-2"
    assert r3.json()["data"]["key"] == "SEQ-3"


@pytest.mark.asyncio
async def test_create_item_with_parent(client: AsyncClient):
    await _create_space(client, "PAR")
    headers = _admin_headers()
    epic = await client.post(
        "/api/v1/spaces/PAR/items",
        json={"title": "Epic", "type": "epic"},
        headers=headers,
    )
    epic_id = epic.json()["data"]["id"]

    story = await client.post(
        "/api/v1/spaces/PAR/items",
        json={"title": "Story under Epic", "type": "story", "parent_id": epic_id},
        headers=headers,
    )
    assert story.status_code == 201
    assert story.json()["data"]["parent_id"] == epic_id


# ── List items ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_items(client: AsyncClient):
    await _create_space(client, "LI")
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/LI/items",
        json={"title": "Item A"},
        headers=headers,
    )
    await client.post(
        "/api/v1/spaces/LI/items",
        json={"title": "Item B"},
        headers=headers,
    )
    response = await client.get("/api/v1/spaces/LI/items", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_list_items_space_not_found(client: AsyncClient):
    response = await client.get("/api/v1/spaces/NOPE/items", headers=_admin_headers())
    assert response.status_code == 404


# ── Get item ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_item(client: AsyncClient):
    await _create_space(client, "GI")
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/GI/items",
        json={"title": "Detail Item", "priority": "high"},
        headers=headers,
    )
    response = await client.get("/api/v1/items/GI-1", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Detail Item"
    assert data["priority"] == "high"
    assert "description" in data
    assert "custom_fields" in data


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient):
    response = await client.get("/api/v1/items/NOPE-999", headers=_admin_headers())
    assert response.status_code == 404


# ── Update item ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_item(client: AsyncClient):
    await _create_space(client, "UI")
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/UI/items",
        json={"title": "Original Title"},
        headers=headers,
    )
    response = await client.put(
        "/api/v1/items/UI-1",
        json={"title": "Updated Title", "priority": "critical"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Updated Title"
    assert data["priority"] == "critical"


# ── Delete item ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient):
    await _create_space(client, "DI")
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/DI/items",
        json={"title": "To Delete"},
        headers=headers,
    )
    response = await client.delete("/api/v1/items/DI-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    # Verify it's gone
    get_resp = await client.get("/api/v1/items/DI-1", headers=headers)
    assert get_resp.status_code == 404


# ── Comments ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_comment(client: AsyncClient):
    await _create_space(client, "CM")
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/CM/items",
        json={"title": "Commented Item"},
        headers=headers,
    )
    response = await client.post(
        "/api/v1/items/CM-1/comments",
        json={"body": {"type": "doc", "content": [{"type": "paragraph", "text": "Great work!"}]}},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["data"]["body"]["type"] == "doc"


@pytest.mark.asyncio
async def test_list_comments(client: AsyncClient):
    await _create_space(client, "LC")
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/LC/items",
        json={"title": "Item with Comments"},
        headers=headers,
    )
    await client.post(
        "/api/v1/items/LC-1/comments",
        json={"body": {"text": "Comment 1"}},
        headers=headers,
    )
    await client.post(
        "/api/v1/items/LC-1/comments",
        json={"body": {"text": "Comment 2"}},
        headers=headers,
    )
    response = await client.get("/api/v1/items/LC-1/comments", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


# ── Worklogs ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_worklog(client: AsyncClient):
    await _create_space(client, "WL")
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/WL/items",
        json={"title": "Logged Item"},
        headers=headers,
    )
    response = await client.post(
        "/api/v1/items/WL-1/worklogs",
        json={"time_spent_seconds": 7200, "description": "Backend work", "log_date": "2026-04-14"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["time_spent_seconds"] == 7200


# ── No auth ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_item_no_auth(client: AsyncClient):
    response = await client.post(
        "/api/v1/spaces/TST/items",
        json={"title": "Sneaky"},
    )
    assert response.status_code in (401, 403)
