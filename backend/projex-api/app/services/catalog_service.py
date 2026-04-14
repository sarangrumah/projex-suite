"""AppCatalog service — CRUD + GitHub webhook → AI doc update pipeline."""

from __future__ import annotations

import hashlib
import hmac
import re
from datetime import datetime, timezone
from fnmatch import fnmatch
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogDocument, CatalogDocVersion, CatalogProduct, CatalogRepository
from app.models.space import Space
from app.schemas.catalog import DocumentCreate, DocumentUpdate, ProductCreate, RepositoryCreate
from app.services.ai_provider import get_ai_provider


class CatalogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Products ────────────────────────────────────────────

    async def create_product(self, space_key: str, data: ProductCreate) -> CatalogProduct:
        space = await self._get_space(space_key)
        product = CatalogProduct(space_id=space.id, name=data.name, description=data.description)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def list_products(self, space_key: str) -> list[CatalogProduct]:
        space = await self._get_space(space_key)
        result = await self.db.execute(
            select(CatalogProduct).where(CatalogProduct.space_id == space.id)
        )
        return list(result.scalars().all())

    # ── Documents ───────────────────────────────────────────

    async def create_document(self, product_id: UUID, data: DocumentCreate) -> CatalogDocument:
        doc = CatalogDocument(
            product_id=product_id, doc_type=data.doc_type, title=data.title,
            body=data.body, code_ownership_map=data.code_ownership_map,
        )
        self.db.add(doc)
        await self.db.flush()
        # Create initial version
        self.db.add(CatalogDocVersion(
            document_id=doc.id, version="1.0.0", change_type="major",
            title=data.title, body=data.body, source="manual", status="published",
        ))
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_documents(self, product_id: UUID) -> list[CatalogDocument]:
        result = await self.db.execute(
            select(CatalogDocument).where(CatalogDocument.product_id == product_id)
        )
        return list(result.scalars().all())

    async def update_document(self, doc_id: UUID, data: DocumentUpdate) -> CatalogDocument:
        result = await self.db.execute(select(CatalogDocument).where(CatalogDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Document not found")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(doc, k, v)
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    # ── Repositories ────────────────────────────────────────

    async def add_repository(self, product_id: UUID, data: RepositoryCreate) -> CatalogRepository:
        repo = CatalogRepository(
            product_id=product_id, repo_url=data.repo_url, webhook_secret=data.webhook_secret,
        )
        self.db.add(repo)
        await self.db.commit()
        await self.db.refresh(repo)
        return repo

    # ── Versions ────────────────────────────────────────────

    async def list_versions(self, doc_id: UUID) -> list[CatalogDocVersion]:
        result = await self.db.execute(
            select(CatalogDocVersion).where(CatalogDocVersion.document_id == doc_id)
            .order_by(CatalogDocVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def approve_version(self, version_id: UUID, status: str, user_id: UUID) -> CatalogDocVersion:
        result = await self.db.execute(select(CatalogDocVersion).where(CatalogDocVersion.id == version_id))
        ver = result.scalar_one_or_none()
        if not ver:
            raise ValueError("Version not found")
        ver.status = status
        ver.reviewed_by = user_id

        # If published, update the main document
        if status == "published":
            doc_result = await self.db.execute(select(CatalogDocument).where(CatalogDocument.id == ver.document_id))
            doc = doc_result.scalar_one_or_none()
            if doc:
                doc.body = ver.body
                doc.title = ver.title
                doc.current_version = ver.version
                doc.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(ver)
        return ver

    # ── GitHub Webhook Pipeline ─────────────────────────────

    def verify_webhook_signature(self, body: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook HMAC-SHA256 signature."""
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def process_merged_pr(self, repo_url: str, pr_data: dict, changed_files: list[str], diff_text: str) -> list[dict]:
        """Process a merged PR: map changed files → docs → AI update → draft version.

        Returns list of created draft versions.
        """
        # Find repository and product
        result = await self.db.execute(
            select(CatalogRepository).where(CatalogRepository.repo_url == repo_url, CatalogRepository.is_active == True)  # noqa: E712
        )
        repo = result.scalar_one_or_none()
        if not repo:
            return []

        # Get all documents for this product
        docs_result = await self.db.execute(
            select(CatalogDocument).where(CatalogDocument.product_id == repo.product_id)
        )
        documents = list(docs_result.scalars().all())
        if not documents:
            return []

        # Extract commit messages
        commit_messages = [pr_data.get("title", "")]
        if pr_data.get("body"):
            commit_messages.append(pr_data["body"][:500])

        # Get AI provider
        ai = get_ai_provider()

        # Classify change type
        change_type = await ai.classify_changes(commit_messages)

        created_versions = []

        for doc in documents:
            # Check if any changed files match the code_ownership_map
            affected_sections = self._match_files_to_sections(changed_files, doc.code_ownership_map)
            if not affected_sections:
                continue

            # Get current doc content as text
            current_content = self._body_to_text(doc.body)

            # Generate AI update
            updated_content = await ai.generate_doc_update(
                current_section=current_content,
                code_diff=diff_text[:5000],
                commit_messages=commit_messages,
            )

            if not updated_content or updated_content.startswith("["):
                continue  # AI failed, skip

            # Bump version
            new_version = self._bump_version(doc.current_version, change_type)

            # Create draft version
            version = CatalogDocVersion(
                document_id=doc.id,
                version=new_version,
                change_type=change_type,
                title=doc.title,
                body={"content": updated_content, "sections_affected": affected_sections},
                source="ai_generated",
                source_ref=pr_data.get("html_url", ""),
                status="draft",
            )
            self.db.add(version)
            created_versions.append({
                "document": doc.title,
                "version": new_version,
                "change_type": change_type,
                "sections": affected_sections,
            })

        if created_versions:
            await self.db.commit()

        return created_versions

    # ── Helpers ──────────────────────────────────────────────

    def _match_files_to_sections(self, changed_files: list[str], ownership_map: dict) -> list[str]:
        """Match changed files against code_ownership_map patterns."""
        sections = []
        for pattern, mapping in ownership_map.items():
            for f in changed_files:
                if fnmatch(f, pattern) or f == pattern:
                    section = mapping.get("section", pattern) if isinstance(mapping, dict) else str(mapping)
                    if section not in sections:
                        sections.append(section)
        return sections

    def _body_to_text(self, body: dict) -> str:
        """Extract text content from doc body."""
        if isinstance(body.get("content"), str):
            return body["content"]
        content = body.get("content", [])
        if isinstance(content, list):
            return "\n".join(
                block.get("text", "") or
                "".join(c.get("text", "") for c in block.get("content", []))
                for block in content
            )
        return str(body)

    def _bump_version(self, current: str, change_type: str) -> str:
        """Bump SemVerDoc version."""
        parts = current.split(".")
        if len(parts) != 3:
            parts = ["1", "0", "0"]
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        if change_type == "major":
            return f"{major + 1}.0.0"
        elif change_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"

    async def _get_space(self, key: str) -> Space:
        result = await self.db.execute(select(Space).where(Space.key == key))
        space = result.scalar_one_or_none()
        if not space:
            raise ValueError(f"Space '{key}' not found")
        return space
