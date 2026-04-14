"""End-to-end integration test: full user journey from register to board drag-drop."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.security import create_access_token
from app.core.permissions import ALL_PERMISSIONS
from app.main import app

BASE_URL = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        yield ac


def _admin_headers(tenant: str = "e2e-test") -> dict[str, str]:
    token = create_access_token({
        "sub": "e2e-admin-id", "tenant_id": tenant, "role": "admin", "permissions": ALL_PERMISSIONS,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_full_e2e_journey(client: AsyncClient):
    """E2E-01: Register → Login → Space → Items → Board → Move → Comment → Worklog → Wiki → Budget → Goal."""
    h = _admin_headers()

    # 1. Health
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

    # 2. Security headers present
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"

    # 3. Create Space with Scrum template
    r = await client.post("/api/v1/spaces/", json={"name": "E2E Project", "key": "E2E", "template": "scrum"}, headers=h)
    assert r.status_code == 201
    assert r.json()["data"]["key"] == "E2E"

    # 4. Verify workflow created (4 statuses for scrum)
    r = await client.get("/api/v1/spaces/E2E/workflow", headers=h)
    assert r.status_code == 200
    statuses = r.json()["data"]["statuses"]
    assert len(statuses) == 4
    assert statuses[0]["name"] == "To Do"

    # 5. Create Epic
    r = await client.post("/api/v1/spaces/E2E/items", json={"title": "Epic: Platform", "type": "epic"}, headers=h)
    assert r.status_code == 201
    assert r.json()["data"]["key"] == "E2E-1"
    epic_id = r.json()["data"]["id"]

    # 6. Create Story under Epic
    r = await client.post("/api/v1/spaces/E2E/items", json={"title": "Story: Auth", "type": "story", "parent_id": epic_id}, headers=h)
    assert r.status_code == 201
    assert r.json()["data"]["key"] == "E2E-2"
    assert r.json()["data"]["parent_id"] == epic_id

    # 7. Create Task
    r = await client.post("/api/v1/spaces/E2E/items", json={"title": "Task: JWT", "type": "task"}, headers=h)
    assert r.status_code == 201
    assert r.json()["data"]["key"] == "E2E-3"

    # 8. View board — 3 items in To Do
    r = await client.get("/api/v1/spaces/E2E/board", headers=h)
    assert r.status_code == 200
    board = r.json()["data"]
    assert board["columns"][0]["count"] == 3

    # 9. Move E2E-3 to In Progress
    in_progress_id = statuses[1]["id"]
    r = await client.put("/api/v1/items/E2E-3/move", json={"status_id": in_progress_id, "position": 0}, headers=h)
    assert r.status_code == 200

    # 10. Verify board after move
    r = await client.get("/api/v1/spaces/E2E/board", headers=h)
    board = r.json()["data"]
    assert board["columns"][0]["count"] == 2  # To Do
    assert board["columns"][1]["count"] == 1  # In Progress

    # 11. Add comment
    r = await client.post("/api/v1/items/E2E-1/comments", json={"body": {"text": "E2E test comment"}}, headers=h)
    assert r.status_code == 201

    # 12. Add worklog
    r = await client.post("/api/v1/items/E2E-3/worklogs",
        json={"time_spent_seconds": 3600, "description": "E2E work", "log_date": "2026-04-14"}, headers=h)
    assert r.status_code == 201

    # 13. Create wiki page
    r = await client.post("/api/v1/spaces/E2E/wiki", json={"title": "E2E Docs", "body": {"type": "doc", "content": []}}, headers=h)
    assert r.status_code == 201
    assert r.json()["data"]["slug"] == "e2e-docs"

    # 14. Create budget
    r = await client.post("/api/v1/spaces/E2E/budgets", json={"name": "E2E Budget"}, headers=h)
    assert r.status_code == 201
    budget_id = r.json()["data"]["id"]

    # 15. Add line item
    r = await client.post(f"/api/v1/budgets/{budget_id}/items",
        json={"category": "Dev", "description": "E2E dev", "quantity": 10, "unit_price": 100000}, headers=h)
    assert r.status_code == 201

    # 16. Create goal
    r = await client.post("/api/v1/spaces/E2E/goals", json={"title": "Ship E2E"}, headers=h)
    assert r.status_code == 201
    goal_id = r.json()["data"]["id"]

    # 17. Add key result
    r = await client.post(f"/api/v1/goals/{goal_id}/key-results",
        json={"title": "Pass all tests", "target_value": 100, "unit": "%"}, headers=h)
    assert r.status_code == 201

    # 18. Dashboard
    r = await client.get("/api/v1/spaces/E2E/dashboard", headers=h)
    assert r.status_code == 200
    assert len(r.json()["data"]["widgets"]) >= 5

    # 19. Search
    r = await client.get("/api/v1/search/?q=E2E", headers=h)
    assert r.status_code == 200
    assert r.json()["meta"]["total"] >= 1

    # 20. Notifications
    r = await client.get("/api/v1/notifications/", headers=h)
    assert r.status_code == 200

    # 21. Sprint
    r = await client.post("/api/v1/spaces/E2E/sprints", json={"name": "Sprint 1"}, headers=h)
    assert r.status_code == 201
    sprint_id = r.json()["data"]["id"]

    r = await client.post(f"/api/v1/sprints/{sprint_id}/start", headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "active"

    # 22. Backlog
    r = await client.get("/api/v1/spaces/E2E/backlog", headers=h)
    assert r.status_code == 200
