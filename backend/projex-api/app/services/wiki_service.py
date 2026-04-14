"""Wiki service — CRUD with version history."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.space import Space
from app.models.wiki import WikiPage, WikiPageVersion
from app.schemas.wiki import WikiPageCreate, WikiPageUpdate


class WikiService:
    """Wiki page CRUD with automatic version snapshots."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, space_key: str, data: WikiPageCreate, user_id: UUID) -> WikiPage:
        """Create a wiki page and its initial version."""
        space = await self._get_space(space_key)
        slug = self._slugify(data.title)

        # Get next position
        count_q = select(func.count()).select_from(WikiPage).where(
            WikiPage.space_id == space.id
        )
        count = (await self.db.execute(count_q)).scalar() or 0

        page = WikiPage(
            space_id=space.id,
            parent_id=data.parent_id,
            title=data.title,
            slug=slug,
            body=data.body,
            position=count,
            created_by=user_id,
        )
        self.db.add(page)
        await self.db.flush()

        # Create version 1
        version = WikiPageVersion(
            page_id=page.id,
            version_num=1,
            title=data.title,
            body=data.body,
            edited_by=user_id,
        )
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def list(self, space_key: str) -> list[WikiPage]:
        """List all wiki pages for a space (tree structure via parent_id)."""
        space = await self._get_space(space_key)
        result = await self.db.execute(
            select(WikiPage)
            .where(WikiPage.space_id == space.id)
            .order_by(WikiPage.position)
        )
        return list(result.scalars().all())

    async def get(self, page_id: UUID) -> WikiPage | None:
        """Get a single wiki page."""
        result = await self.db.execute(
            select(WikiPage).where(WikiPage.id == page_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, space_key: str, slug: str) -> WikiPage | None:
        """Get a wiki page by space key and slug."""
        space = await self._get_space(space_key)
        result = await self.db.execute(
            select(WikiPage).where(
                WikiPage.space_id == space.id,
                WikiPage.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, page_id: UUID, data: WikiPageUpdate, user_id: UUID) -> WikiPage:
        """Update a wiki page and create a new version snapshot."""
        page = await self.get(page_id)
        if not page:
            raise ValueError("Wiki page not found")

        update_data = data.model_dump(exclude_unset=True)
        changed = False

        if "title" in update_data:
            page.title = update_data["title"]
            page.slug = self._slugify(update_data["title"])
            changed = True
        if "body" in update_data:
            page.body = update_data["body"]
            changed = True
        if "parent_id" in update_data:
            page.parent_id = update_data["parent_id"]
        if "position" in update_data:
            page.position = update_data["position"]

        page.updated_by = user_id
        page.updated_at = datetime.now(timezone.utc)

        # Create new version if content changed
        if changed:
            last_ver = await self._get_latest_version_num(page.id)
            version = WikiPageVersion(
                page_id=page.id,
                version_num=last_ver + 1,
                title=page.title,
                body=page.body,
                edited_by=user_id,
            )
            self.db.add(version)

        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def delete(self, page_id: UUID) -> None:
        """Delete a wiki page and its versions."""
        page = await self.get(page_id)
        if not page:
            raise ValueError("Wiki page not found")

        # Delete versions first
        versions = await self.db.execute(
            select(WikiPageVersion).where(WikiPageVersion.page_id == page_id)
        )
        for v in versions.scalars().all():
            await self.db.delete(v)

        await self.db.delete(page)
        await self.db.commit()

    async def get_versions(self, page_id: UUID) -> list[WikiPageVersion]:
        """Get version history for a page."""
        result = await self.db.execute(
            select(WikiPageVersion)
            .where(WikiPageVersion.page_id == page_id)
            .order_by(WikiPageVersion.version_num.desc())
        )
        return list(result.scalars().all())

    async def _get_space(self, key: str) -> Space:
        result = await self.db.execute(select(Space).where(Space.key == key))
        space = result.scalar_one_or_none()
        if not space:
            raise ValueError(f"Space '{key}' not found")
        return space

    async def _get_latest_version_num(self, page_id: UUID) -> int:
        result = await self.db.execute(
            select(func.max(WikiPageVersion.version_num)).where(
                WikiPageVersion.page_id == page_id
            )
        )
        return result.scalar() or 0

    def _slugify(self, title: str) -> str:
        slug = title.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug[:500]
