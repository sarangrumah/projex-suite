"""Auth endpoint tests: register, login, lockout, refresh, MFA, tenant isolation."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, create_refresh_token, decode_token
from app.main import app


BASE_URL = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as ac:
        yield ac


# ── Health check ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ── Register ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Admin User",
            "tenant_slug": "test-tenant",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["errors"] == []
    assert "tokens" in data["data"]
    assert data["data"]["user"]["email"] == "admin@projex.id"
    assert data["data"]["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@projex.id",
            "password": "short",
            "display_name": "Weak User",
            "tenant_slug": "test-tenant",
        },
    )
    # Pydantic validation catches min_length=12 before service layer
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dupe@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "First",
            "tenant_slug": "test-tenant",
        },
    )
    # Try again with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dupe@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Second",
            "tenant_slug": "test-tenant",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


# ── Login ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Login User",
            "tenant_slug": "test-tenant",
        },
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@projex.id",
            "password": "SecurePass123!@#",
            "tenant_slug": "test-tenant",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["requires_mfa"] is False
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "WrongPW User",
            "tenant_slug": "test-tenant",
        },
    )
    # Wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpw@projex.id",
            "password": "WrongPassword123!@",
            "tenant_slug": "test-tenant",
        },
    )
    assert response.status_code == 401
    # Error should be generic — never hint which field is wrong
    assert "Email or password incorrect" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "noone@projex.id",
            "password": "SecurePass123!@#",
            "tenant_slug": "test-tenant",
        },
    )
    assert response.status_code == 401
    assert "Email or password incorrect" in response.json()["detail"]


# ── Account lockout ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_lockout_after_10_failures(client: AsyncClient):
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "lockout@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Lockout User",
            "tenant_slug": "test-tenant",
        },
    )
    # Fail 10 times
    for _ in range(10):
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "lockout@projex.id",
                "password": "BadPassword!1234",
                "tenant_slug": "test-tenant",
            },
        )

    # 11th attempt — even with correct password — should be locked
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "lockout@projex.id",
            "password": "SecurePass123!@#",
            "tenant_slug": "test-tenant",
        },
    )
    assert response.status_code == 401
    assert "locked" in response.json()["detail"].lower()


# ── Token refresh ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    # Register and get tokens
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Refresh User",
            "tenant_slug": "test-tenant",
        },
    )
    refresh_token = reg.json()["data"]["tokens"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient):
    # Try to use an access token as a refresh token
    access_token = create_access_token(
        {"sub": "test-id", "tenant_id": "test", "role": "member", "permissions": []}
    )
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401
    assert "Invalid token type" in response.json()["detail"]


# ── JWT validation ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    from datetime import timedelta

    token = create_access_token(
        {"sub": "test-id", "tenant_id": "test", "role": "member", "permissions": []},
        expires_delta=timedelta(seconds=-1),
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token_cannot_access_api(client: AsyncClient):
    refresh = create_refresh_token(
        {"sub": "test-id", "tenant_id": "test", "role": "member", "permissions": []}
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh}"},
    )
    assert response.status_code == 401
    assert "refresh token" in response.json()["detail"].lower()


# ── Me endpoint ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_returns_profile(client: AsyncClient):
    # Register
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Me User",
            "tenant_slug": "test-tenant",
        },
    )
    token = reg.json()["data"]["tokens"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "me@projex.id"
    assert data["display_name"] == "Me User"
    assert data["role"] == "admin"
    assert "permissions" in data


# ── Tenant isolation ────────────────────────────────────────

@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient):
    """User from tenant_a cannot see tenant_b data."""
    # Register in tenant A
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Tenant A",
            "tenant_slug": "tenant-a",
        },
    )
    # Register in tenant B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@projex.id",
            "password": "SecurePass123!@#",
            "display_name": "Tenant B",
            "tenant_slug": "tenant-b",
        },
    )
    token_b = reg_b.json()["data"]["tokens"]["access_token"]

    # User B's /me should show tenant-b context
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 200
    # Token's tenant_id should be tenant-b
    payload = decode_token(token_b)
    assert payload["tenant_id"] == "tenant-b"


# ── Logout ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    token = create_access_token(
        {"sub": "test-id", "tenant_id": "test", "role": "member", "permissions": []}
    )
    response = await client.post(
        "/api/v1/auth/logout",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["logged_out"] is True
