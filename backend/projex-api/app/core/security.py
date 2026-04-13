"""Security utilities: JWT, password hashing, PII encryption, input sanitization."""

import hashlib
import html
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# --- Password hashing (bcrypt cost=12) ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """Hash a password with bcrypt cost=12."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT (RS256) ---


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": str(uuid4())})
    return jwt.encode(to_encode, settings.jwt_private_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token with 7-day expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update(
        {"exp": expire, "iat": datetime.now(timezone.utc), "jti": str(uuid4()), "type": "refresh"}
    )
    return jwt.encode(to_encode, settings.jwt_private_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm])


# --- PII Encryption (AES-256 via Fernet) ---

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Lazy-init Fernet cipher from config key."""
    global _fernet
    if _fernet is None:
        # Fernet requires a 32-byte URL-safe base64 key
        # Derive one from the configured encryption_key
        import base64

        key_bytes = hashlib.sha256(settings.encryption_key.encode()).digest()
        _fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    return _fernet


def encrypt_pii(value: str) -> str:
    """Encrypt a PII value (email, phone, NPWP) for database storage."""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_pii(encrypted_value: str) -> str:
    """Decrypt a PII value from database storage."""
    return _get_fernet().decrypt(encrypted_value.encode()).decode()


# --- Password strength validation ---

_PASSWORD_MIN_LENGTH = 12


def validate_password_strength(password: str) -> list[str]:
    """Validate password complexity. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    if len(password) < _PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {_PASSWORD_MIN_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    return errors


# --- Device fingerprint ---


def generate_device_fingerprint(user_agent: str, ip_address: str) -> str:
    """Generate a device fingerprint from user-agent + IP."""
    raw = f"{user_agent}:{ip_address}"
    return hashlib.sha256(raw.encode()).hexdigest()


# --- Input sanitization ---


def sanitize_input(text: str) -> str:
    """Strip potential XSS patterns from user text input."""
    return html.escape(text, quote=True)
