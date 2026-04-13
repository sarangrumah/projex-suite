"""Authentication service — business logic for register, login, MFA, tokens."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_pii,
    encrypt_pii,
    generate_device_fingerprint,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MFASetupResponse,
    RegisterRequest,
    TokenResponse,
)

# Login lockout thresholds
_CAPTCHA_THRESHOLD = 3
_LOCKOUT_THRESHOLD = 10
_LOCKOUT_DURATION_MINUTES = 15


class AuthService:
    """Handles authentication business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Register ────────────────────────────────────────────

    async def register(self, data: RegisterRequest) -> tuple[User, TokenResponse]:
        """Create a new user account and return tokens."""
        # Validate password strength
        errors = validate_password_strength(data.password)
        if errors:
            raise ValueError("; ".join(errors))

        # Check duplicate email
        existing = await self._get_user_by_email(data.email)
        if existing:
            raise ValueError("An account with this email already exists")

        # Create user
        user = User(
            email=data.email,
            email_encrypted=encrypt_pii(data.email),
            password_hash=hash_password(data.password),
            display_name=data.display_name,
            role="admin",  # First user in tenant gets admin
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        tokens = self._generate_tokens(user, data.tenant_slug)
        return user, tokens

    # ── Login ───────────────────────────────────────────────

    async def login(self, data: LoginRequest) -> tuple[User, TokenResponse, bool]:
        """Authenticate user. Returns (user, tokens, requires_mfa).

        Raises ValueError with generic message on failure (never hints which field is wrong).
        """
        user = await self._get_user_by_email(data.email)

        if not user or not user.is_active:
            raise ValueError("Email or password incorrect")

        # Check lockout
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds())
            raise ValueError(f"Account locked. Try again in {remaining} seconds")

        # Verify password
        if not verify_password(data.password, user.password_hash):
            await self._record_failed_login(user)
            raise ValueError("Email or password incorrect")

        # Reset failed count on success
        user.failed_login_count = 0
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Check MFA
        if user.mfa_enabled:
            # Return partial token — frontend must call /mfa/verify
            return user, self._generate_tokens(user, data.tenant_slug), True

        tokens = self._generate_tokens(user, data.tenant_slug)
        return user, tokens, False

    # ── MFA ─────────────────────────────────────────────────

    async def setup_mfa(self, user_id: UUID) -> MFASetupResponse:
        """Generate TOTP secret and QR URI for MFA setup."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        secret = pyotp.random_base32()
        user.mfa_secret_encrypted = encrypt_pii(secret)
        await self.db.commit()

        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="ProjeX Suite",
        )
        return MFASetupResponse(secret=secret, qr_uri=qr_uri)

    async def verify_mfa(self, user_id: UUID, code: str) -> bool:
        """Verify TOTP code and enable MFA if valid."""
        user = await self._get_user_by_id(user_id)
        if not user or not user.mfa_secret_encrypted:
            raise ValueError("MFA not configured")

        secret = decrypt_pii(user.mfa_secret_encrypted)
        totp = pyotp.TOTP(secret)

        if not totp.verify(code, valid_window=1):
            return False

        if not user.mfa_enabled:
            user.mfa_enabled = True
            await self.db.commit()

        return True

    # ── Token refresh ───────────────────────────────────────

    async def refresh_tokens(
        self, user_id: str, tenant_slug: str
    ) -> TokenResponse:
        """Generate new token pair from refresh token (rotation)."""
        user = await self._get_user_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise ValueError("Invalid refresh token")

        return self._generate_tokens(user, tenant_slug)

    # ── Profile ─────────────────────────────────────────────

    async def get_profile(self, user_id: UUID) -> User:
        """Get user profile by ID."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    # ── Private helpers ─────────────────────────────────────

    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _record_failed_login(self, user: User) -> None:
        """Increment failed login count, lock account if threshold reached."""
        user.failed_login_count += 1

        if user.failed_login_count >= _LOCKOUT_THRESHOLD:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=_LOCKOUT_DURATION_MINUTES
            )

        await self.db.commit()

    def _generate_tokens(self, user: User, tenant_slug: str) -> TokenResponse:
        """Create JWT access + refresh token pair."""
        payload = {
            "sub": str(user.id),
            "tenant_id": tenant_slug,
            "role": user.role,
            "permissions": self._get_permissions_for_role(user.role),
        }
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    def _get_permissions_for_role(self, role: str) -> list[str]:
        """Get permission list for a built-in role."""
        from app.core.permissions import DEFAULT_ROLES

        role_def = DEFAULT_ROLES.get(role, {})
        return role_def.get("permissions", [])
