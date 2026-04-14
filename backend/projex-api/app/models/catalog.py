"""AppCatalog models — product registry, documents, versions, repositories."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CatalogProduct(Base):
    """A software product registered in the catalog."""

    __tablename__ = "catalog_products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    documents: Mapped[list[CatalogDocument]] = relationship(back_populates="product")
    repositories: Mapped[list[CatalogRepository]] = relationship(back_populates="product")


class CatalogDocument(Base):
    """A document (BRD/FSD/TSD/etc) linked to a product."""

    __tablename__ = "catalog_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog_products.id"), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False)  # brd | fsd | tsd | data_dict | api_spec | security
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    current_version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="1.0.0")  # SemVerDoc
    body: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    code_ownership_map: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    # Maps file patterns to doc sections: {"src/api/auth.py": {"section": "5.1 Auth"}}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    product: Mapped[CatalogProduct] = relationship(back_populates="documents")
    versions: Mapped[list[CatalogDocVersion]] = relationship(back_populates="document")


class CatalogDocVersion(Base):
    """SemVerDoc version snapshot — immutable history of document changes."""

    __tablename__ = "catalog_doc_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog_documents.id"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "1.2.0"
    change_type: Mapped[str] = mapped_column(String(10), nullable=False)  # major | minor | patch
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default="manual")  # manual | ai_generated
    source_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)  # PR URL
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")  # draft | approved | published
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    document: Mapped[CatalogDocument] = relationship(back_populates="versions")


class CatalogRepository(Base):
    """GitHub repository linked to a product for webhook processing."""

    __tablename__ = "catalog_repositories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog_products.id"), nullable=False, index=True)
    repo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    product: Mapped[CatalogProduct] = relationship(back_populates="repositories")
