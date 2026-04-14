"""Custom field service — CRUD + validation for field definitions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_field import CustomFieldDefinition
from app.models.space import Space
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate


class CustomFieldService:
    """Manages custom field definitions per space."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, space_key: str, data: CustomFieldCreate) -> CustomFieldDefinition:
        """Create a custom field definition for a space."""
        space = await self._get_space(space_key)

        # Validate config for type
        self._validate_config(data.field_type, data.config)

        # Get next position
        count_q = select(func.count()).select_from(CustomFieldDefinition).where(
            CustomFieldDefinition.space_id == space.id
        )
        count = (await self.db.execute(count_q)).scalar() or 0

        field = CustomFieldDefinition(
            space_id=space.id,
            name=data.name,
            field_type=data.field_type,
            description=data.description,
            is_required=data.is_required,
            position=count,
            config=data.config,
        )
        self.db.add(field)
        await self.db.commit()
        await self.db.refresh(field)
        return field

    async def list(self, space_key: str) -> list[CustomFieldDefinition]:
        """List all custom field definitions for a space."""
        space = await self._get_space(space_key)
        result = await self.db.execute(
            select(CustomFieldDefinition)
            .where(CustomFieldDefinition.space_id == space.id)
            .order_by(CustomFieldDefinition.position)
        )
        return list(result.scalars().all())

    async def get(self, field_id: UUID) -> CustomFieldDefinition | None:
        """Get a single custom field definition."""
        result = await self.db.execute(
            select(CustomFieldDefinition).where(CustomFieldDefinition.id == field_id)
        )
        return result.scalar_one_or_none()

    async def update(self, field_id: UUID, data: CustomFieldUpdate) -> CustomFieldDefinition:
        """Update a custom field definition."""
        field = await self.get(field_id)
        if not field:
            raise ValueError("Custom field not found")

        update_data = data.model_dump(exclude_unset=True)
        if "config" in update_data:
            self._validate_config(field.field_type, update_data["config"])

        for k, v in update_data.items():
            setattr(field, k, v)

        await self.db.commit()
        await self.db.refresh(field)
        return field

    async def delete(self, field_id: UUID) -> None:
        """Delete a custom field definition."""
        field = await self.get(field_id)
        if not field:
            raise ValueError("Custom field not found")
        await self.db.delete(field)
        await self.db.commit()

    async def validate_item_custom_fields(
        self, space_id: UUID, custom_fields: dict[str, Any]
    ) -> list[str]:
        """Validate work item custom field values against definitions.

        Returns list of error messages (empty = valid).
        """
        result = await self.db.execute(
            select(CustomFieldDefinition).where(CustomFieldDefinition.space_id == space_id)
        )
        definitions = {str(f.id): f for f in result.scalars().all()}
        errors: list[str] = []

        # Check required fields
        for fid, defn in definitions.items():
            if defn.is_required and fid not in custom_fields:
                errors.append(f"Field '{defn.name}' is required")

        # Validate values against type
        for fid, value in custom_fields.items():
            defn = definitions.get(fid)
            if not defn:
                continue

            if defn.field_type == "select":
                options = defn.config.get("options", [])
                if value not in options:
                    errors.append(f"'{defn.name}' must be one of: {', '.join(options)}")

            elif defn.field_type == "multi_select":
                options = defn.config.get("options", [])
                if isinstance(value, list):
                    invalid = [v for v in value if v not in options]
                    if invalid:
                        errors.append(f"'{defn.name}' invalid values: {', '.join(invalid)}")

            elif defn.field_type == "number":
                if not isinstance(value, (int, float)):
                    errors.append(f"'{defn.name}' must be a number")

            elif defn.field_type == "checkbox":
                if not isinstance(value, bool):
                    errors.append(f"'{defn.name}' must be true or false")

        return errors

    def _validate_config(self, field_type: str, config: dict) -> None:
        """Validate type-specific config."""
        if field_type in ("select", "multi_select"):
            if "options" not in config or not isinstance(config["options"], list):
                raise ValueError(f"'{field_type}' requires config.options array")
            if len(config["options"]) < 1:
                raise ValueError("At least one option is required")

        elif field_type == "formula":
            if "expression" not in config:
                raise ValueError("Formula field requires config.expression")

        elif field_type == "rollup":
            if "source_field" not in config or "aggregation" not in config:
                raise ValueError("Rollup field requires config.source_field and config.aggregation")

    async def _get_space(self, key: str) -> Space:
        result = await self.db.execute(select(Space).where(Space.key == key))
        space = result.scalar_one_or_none()
        if not space:
            raise ValueError(f"Space '{key}' not found")
        return space
