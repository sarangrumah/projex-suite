"""Audit middleware — log CREATE, UPDATE, DELETE actions with hash-chain integrity."""

import hashlib
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.audit import AuditEvent


async def create_audit_entry(
    actor_id: str,
    actor_ip: str,
    action: str,
    resource_type: str,
    resource_id: str,
    tenant_id: str | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
) -> None:
    """Create a hash-chained audit log entry.

    Each entry's hash = SHA256(payload + prev_hash), forming an append-only chain.
    """
    async with async_session_factory() as session:
        try:
            # Ensure audit schema exists
            await session.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))

            # Get previous hash
            prev_hash = await _get_last_hash(session)

            # Build payload
            payload = {
                "actor_id": actor_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "before_hash": _hash_state(before_state),
                "after_hash": _hash_state(after_state),
            }

            # Compute entry hash
            canonical = json.dumps(payload, sort_keys=True) + (prev_hash or "GENESIS")
            entry_hash = hashlib.sha256(canonical.encode()).hexdigest()

            event = AuditEvent(
                prev_hash=prev_hash,
                entry_hash=entry_hash,
                actor_id=actor_id,
                actor_ip=actor_ip,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                tenant_id=tenant_id,
                before_state=before_state,
                after_state=after_state,
            )
            session.add(event)
            await session.commit()
        except Exception:
            # Audit failures should not break the main request
            await session.rollback()


async def _get_last_hash(session: AsyncSession) -> str | None:
    """Get the entry_hash of the most recent audit event."""
    try:
        result = await session.execute(
            select(AuditEvent.entry_hash)
            .order_by(AuditEvent.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row
    except Exception:
        return None


def _hash_state(state: dict[str, Any] | None) -> str | None:
    """SHA256 hash of a state dict for before/after comparison."""
    if state is None:
        return None
    return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()


async def verify_chain_integrity() -> tuple[bool, int]:
    """Verify the entire audit chain. Returns (is_valid, checked_count)."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditEvent).order_by(AuditEvent.created_at)
        )
        events = list(result.scalars().all())

        if not events:
            return True, 0

        for i, event in enumerate(events):
            expected_prev = events[i - 1].entry_hash if i > 0 else None
            if event.prev_hash != expected_prev:
                return False, i

            # Recompute hash
            payload = {
                "actor_id": event.actor_id,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "before_hash": _hash_state(event.before_state),
                "after_hash": _hash_state(event.after_state),
            }
            canonical = json.dumps(payload, sort_keys=True) + (event.prev_hash or "GENESIS")
            expected_hash = hashlib.sha256(canonical.encode()).hexdigest()

            if event.entry_hash != expected_hash:
                return False, i

        return True, len(events)
