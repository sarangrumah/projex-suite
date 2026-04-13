"""Shared test fixtures for ProjeX API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


async def get_auth_headers(
    role: str = "member",
    tenant: str = "tenant_test",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Generate auth headers with a valid JWT for testing."""
    if permissions is None:
        permissions = [
            "space:create", "space:edit",
            "item:create", "item:edit",
            "sprint:create",
        ]
    token = create_access_token(
        data={
            "sub": "test-user-id",
            "tenant_id": tenant,
            "role": role,
            "permissions": permissions,
        }
    )
    return {"Authorization": f"Bearer {token}"}
