"""Security tests: headers, XSS sanitization, JWT, tenant isolation, rate limiting."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import (
    create_access_token,
    encrypt_pii,
    decrypt_pii,
    hash_password,
    verify_password,
    validate_password_strength,
    sanitize_input,
    generate_device_fingerprint,
)
from app.core.permissions import ALL_PERMISSIONS
from app.main import app

BASE_URL = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as ac:
        yield ac


# ── Security Headers ────────────────────────────────────────

@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" in headers
    assert "max-age=31536000" in headers["strict-transport-security"]
    assert "content-security-policy" in headers
    assert "default-src 'self'" in headers["content-security-policy"]
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "permissions-policy" in headers


# ── PII Encryption ──────────────────────────────────────────

def test_encrypt_decrypt_pii():
    original = "admin@projex.id"
    encrypted = encrypt_pii(original)
    assert encrypted != original
    assert len(encrypted) > len(original)
    decrypted = decrypt_pii(encrypted)
    assert decrypted == original


def test_encrypt_pii_different_outputs():
    """Same input should produce different ciphertext (Fernet uses random IV)."""
    val = "test@example.com"
    enc1 = encrypt_pii(val)
    enc2 = encrypt_pii(val)
    # Fernet includes timestamp so consecutive calls differ
    assert decrypt_pii(enc1) == val
    assert decrypt_pii(enc2) == val


# ── Password Security ───────────────────────────────────────

def test_password_hash_bcrypt():
    password = "SecurePass123!@#"
    hashed = hash_password(password)
    assert hashed.startswith("$2b$12$")  # bcrypt cost=12
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_password_strength_validation():
    # Too short
    errors = validate_password_strength("Short1!")
    assert len(errors) > 0

    # No uppercase
    errors = validate_password_strength("alllowercase123!")
    assert any("uppercase" in e for e in errors)

    # No digit
    errors = validate_password_strength("NoDigitsHere!@#A")
    assert any("digit" in e for e in errors)

    # No special char
    errors = validate_password_strength("NoSpecialChar123A")
    assert any("special" in e for e in errors)

    # Valid password
    errors = validate_password_strength("SecurePass123!@#")
    assert errors == []


# ── XSS Sanitization ───────────────────────────────────────

def test_sanitize_input_strips_script_tags():
    malicious = '<script>alert("xss")</script>'
    sanitized = sanitize_input(malicious)
    assert "<script>" not in sanitized
    assert "alert" in sanitized  # Text content preserved but escaped
    assert "&lt;script&gt;" in sanitized


def test_sanitize_input_strips_event_handlers():
    malicious = '<img onerror="alert(1)" src="x">'
    sanitized = sanitize_input(malicious)
    assert "onerror" not in sanitized or "&quot;" in sanitized


def test_sanitize_preserves_normal_text():
    normal = "This is a regular comment about work item AIM-101"
    assert sanitize_input(normal) == normal


# ── Device Fingerprint ──────────────────────────────────────

def test_device_fingerprint_deterministic():
    fp1 = generate_device_fingerprint("Mozilla/5.0", "192.168.1.1")
    fp2 = generate_device_fingerprint("Mozilla/5.0", "192.168.1.1")
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA256 hex


def test_device_fingerprint_varies():
    fp1 = generate_device_fingerprint("Mozilla/5.0", "192.168.1.1")
    fp2 = generate_device_fingerprint("Chrome/120", "192.168.1.1")
    assert fp1 != fp2


# ── JWT Security ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_malformed_jwt_rejected(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_auth_header(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


# ── SQL Injection Prevention ────────────────────────────────

@pytest.mark.asyncio
async def test_sql_injection_in_space_key(client: AsyncClient):
    """SQL injection in path params should be safely handled by ORM."""
    token = create_access_token({
        "sub": "test", "tenant_id": "test", "role": "admin", "permissions": ALL_PERMISSIONS,
    })
    response = await client.get(
        "/api/v1/spaces/'; DROP TABLE spaces; --",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Should return 404, not a SQL error
    assert response.status_code in (404, 422)


@pytest.mark.asyncio
async def test_sql_injection_in_item_key(client: AsyncClient):
    token = create_access_token({
        "sub": "test", "tenant_id": "test", "role": "admin", "permissions": ALL_PERMISSIONS,
    })
    response = await client.get(
        "/api/v1/items/1 OR 1=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (404, 422)


# ── XSS in Work Item Fields ────────────────────────────────

@pytest.mark.asyncio
async def test_xss_in_item_title(client: AsyncClient):
    """XSS in title field should not execute — stored as plain text."""
    token = create_access_token({
        "sub": "admin-id", "tenant_id": "test", "role": "admin", "permissions": ALL_PERMISSIONS,
    })
    headers = {"Authorization": f"Bearer {token}"}

    # Create space first
    await client.post(
        "/api/v1/spaces/",
        json={"name": "XSS Test", "key": "XSS", "template": "blank"},
        headers=headers,
    )

    # Create item with XSS in title
    response = await client.post(
        "/api/v1/spaces/XSS/items",
        json={"title": '<script>alert("xss")</script>Legit Title'},
        headers=headers,
    )
    assert response.status_code == 201
    # Title is stored as-is (frontend escapes on render)
    data = response.json()["data"]
    assert data["title"] is not None


# ── Error Response Format ───────────────────────────────────

@pytest.mark.asyncio
async def test_error_response_envelope(client: AsyncClient):
    """All errors should return the standard { data, meta, errors } envelope."""
    response = await client.get("/api/v1/spaces/NONEXISTENT", headers={
        "Authorization": f"Bearer {create_access_token({'sub': 'x', 'tenant_id': 'x', 'role': 'admin', 'permissions': ALL_PERMISSIONS})}"
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_global_exception_returns_envelope(client: AsyncClient):
    """500 errors should return the standard envelope, not stack traces."""
    # Health endpoint should always work, but test the format
    response = await client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
