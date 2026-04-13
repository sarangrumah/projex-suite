"""RBAC tests: permission checks, role-based access, field-level security."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.permissions import ALL_PERMISSIONS, DEFAULT_ROLES, Permissions
from app.core.security import create_access_token
from app.main import app
from app.middleware.rbac import filter_fields_for_role

BASE_URL = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as ac:
        yield ac


# ── Permission constants ────────────────────────────────────

def test_all_permissions_populated():
    assert len(ALL_PERMISSIONS) > 10
    assert Permissions.SPACE_CREATE in ALL_PERMISSIONS
    assert Permissions.ADMIN_SETTINGS in ALL_PERMISSIONS


def test_default_roles_exist():
    assert "admin" in DEFAULT_ROLES
    assert "member" in DEFAULT_ROLES
    assert "viewer" in DEFAULT_ROLES
    assert "guest" in DEFAULT_ROLES


def test_admin_has_all_permissions():
    admin = DEFAULT_ROLES["admin"]
    assert set(admin["permissions"]) == set(ALL_PERMISSIONS)


def test_member_cannot_delete_spaces():
    member = DEFAULT_ROLES["member"]
    assert Permissions.SPACE_DELETE not in member["permissions"]
    assert Permissions.ADMIN_USERS not in member["permissions"]


def test_viewer_is_read_only():
    viewer = DEFAULT_ROLES["viewer"]
    assert Permissions.ITEM_CREATE not in viewer["permissions"]
    assert Permissions.SPACE_CREATE not in viewer["permissions"]
    assert Permissions.ITEM_COMMENT in viewer["permissions"]


def test_guest_minimal_permissions():
    guest = DEFAULT_ROLES["guest"]
    assert len(guest["permissions"]) <= 2
    assert Permissions.ITEM_COMMENT in guest["permissions"]


# ── Field-level security ────────────────────────────────────

def test_filter_fields_admin_sees_all():
    data = {"name": "Test", "budget_amount": 50000, "timesheet_rate": 100}
    result = filter_fields_for_role(data, "admin")
    assert "budget_amount" in result
    assert "timesheet_rate" in result


def test_filter_fields_viewer_hides_budget():
    data = {"name": "Test", "budget_amount": 50000}
    result = filter_fields_for_role(data, "viewer")
    assert "budget_amount" not in result
    assert result["name"] == "Test"


def test_filter_fields_guest_hides_budget_and_rate():
    data = {"name": "Test", "budget_amount": 50000, "timesheet_rate": 100}
    result = filter_fields_for_role(data, "guest")
    assert "budget_amount" not in result
    assert "timesheet_rate" not in result
    assert result["name"] == "Test"


def test_filter_fields_handles_list():
    data = [
        {"name": "A", "budget_amount": 100},
        {"name": "B", "budget_amount": 200},
    ]
    result = filter_fields_for_role(data, "viewer")
    assert len(result) == 2
    assert "budget_amount" not in result[0]
    assert "budget_amount" not in result[1]


# ── API permission enforcement ──────────────────────────────

@pytest.mark.asyncio
async def test_admin_can_access_protected_endpoint(client: AsyncClient):
    token = create_access_token({
        "sub": "admin-id",
        "tenant_id": "test",
        "role": "admin",
        "permissions": ALL_PERMISSIONS,
    })
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    # May 404 if user not in DB, but NOT 403
    assert response.status_code != 403


@pytest.mark.asyncio
async def test_no_token_returns_401_or_403(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
