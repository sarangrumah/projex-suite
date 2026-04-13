"""Board + workflow endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.core.permissions import ALL_PERMISSIONS
from app.main import app

BASE_URL = "http://test"


def _admin_headers() -> dict[str, str]:
    token = create_access_token({
        "sub": "admin-user-id",
        "tenant_id": "test-tenant",
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


async def _setup_space_with_items(client: AsyncClient, key: str = "BD"):
    """Create a space with scrum template and add items."""
    headers = _admin_headers()
    await client.post(
        "/api/v1/spaces/",
        json={"name": "Board Space", "key": key, "template": "scrum"},
        headers=headers,
    )
    await client.post(
        "/api/v1/spaces/{}/items".format(key),
        json={"title": "Epic: Drone", "type": "epic"},
        headers=headers,
    )
    await client.post(
        "/api/v1/spaces/{}/items".format(key),
        json={"title": "Story: Takeoff", "type": "story"},
        headers=headers,
    )
    await client.post(
        "/api/v1/spaces/{}/items".format(key),
        json={"title": "Task: Calibrate", "type": "task"},
        headers=headers,
    )


# ── Board endpoint ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_board(client: AsyncClient):
    await _setup_space_with_items(client, "BD")
    response = await client.get("/api/v1/spaces/BD/board", headers=_admin_headers())
    assert response.status_code == 200
    data = response.json()["data"]

    # Scrum template has 4 columns
    assert len(data["columns"]) == 4
    assert data["columns"][0]["status"]["name"] == "To Do"
    assert data["columns"][0]["status"]["category"] == "todo"
    assert data["columns"][3]["status"]["name"] == "Done"

    # All 3 items should be in first column (initial status)
    assert data["columns"][0]["count"] == 3

    # Quick filters should have data
    assert "quick_filters" in data
    assert "types" in data["quick_filters"]


@pytest.mark.asyncio
async def test_get_board_not_found(client: AsyncClient):
    response = await client.get("/api/v1/spaces/NOPE/board", headers=_admin_headers())
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_board_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/spaces/BD/board")
    assert response.status_code in (401, 403)


# ── Workflow endpoint ───────────────────────────────────────

@pytest.mark.asyncio
async def test_get_workflow(client: AsyncClient):
    await _setup_space_with_items(client, "WF")
    response = await client.get("/api/v1/spaces/WF/workflow", headers=_admin_headers())
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["work_item_type"] == "all"
    assert len(data["statuses"]) == 4
    assert data["statuses"][0]["name"] == "To Do"
    assert data["statuses"][0]["category"] == "todo"

    # Transitions should be defined
    assert "transitions" in data["definition"]
    assert len(data["definition"]["transitions"]) > 0


@pytest.mark.asyncio
async def test_get_workflow_not_found(client: AsyncClient):
    response = await client.get("/api/v1/spaces/NOPE/workflow", headers=_admin_headers())
    assert response.status_code == 404


# ── Item move (board drag-drop) ─────────────────────────────

@pytest.mark.asyncio
async def test_move_item(client: AsyncClient):
    await _setup_space_with_items(client, "MV")
    headers = _admin_headers()

    # Get workflow to find status IDs
    wf_resp = await client.get("/api/v1/spaces/MV/workflow", headers=headers)
    statuses = wf_resp.json()["data"]["statuses"]
    in_progress_id = statuses[1]["id"]  # "In Progress"

    # Move item to "In Progress"
    response = await client.put(
        "/api/v1/items/MV-1/move",
        json={"status_id": in_progress_id, "position": 0},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status_id"] == in_progress_id

    # Verify board reflects the move
    board_resp = await client.get("/api/v1/spaces/MV/board", headers=headers)
    board = board_resp.json()["data"]
    # To Do should have 2 items now
    assert board["columns"][0]["count"] == 2
    # In Progress should have 1 item
    assert board["columns"][1]["count"] == 1
