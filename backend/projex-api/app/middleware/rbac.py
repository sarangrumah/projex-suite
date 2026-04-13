"""RBAC middleware: field-level security filtering on API responses."""

import copy
from typing import Any

from app.core.permissions import DEFAULT_ROLES


def filter_fields_for_role(data: dict[str, Any] | list, role: str) -> dict[str, Any] | list:
    """Remove or mask fields based on role's field_security config."""
    role_def = DEFAULT_ROLES.get(role)
    if not role_def:
        return data

    field_security = role_def.get("field_security", {})
    if not field_security:
        return data

    if isinstance(data, list):
        return [_filter_single(item, field_security) for item in data]
    return _filter_single(data, field_security)


def _filter_single(item: dict[str, Any], field_security: dict[str, str]) -> dict[str, Any]:
    """Apply field security to a single dict."""
    if not isinstance(item, dict):
        return item

    result = copy.copy(item)
    for field, access in field_security.items():
        if field in result:
            if access == "hidden":
                del result[field]
            elif access == "read_only":
                pass  # Keep value but mark as read-only (handled by frontend)
    return result
