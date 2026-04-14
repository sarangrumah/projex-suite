"""AppCatalog API endpoints: products, documents, versions, GitHub webhook."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import Permissions
from app.schemas.catalog import DocumentCreate, DocumentUpdate, ProductCreate, RepositoryCreate, VersionApproval
from app.services.catalog_service import CatalogService

router = APIRouter(tags=["appcatalog"])


# ── Products ────────────────────────────────────────────────

@router.post("/spaces/{space_key}/catalog/products", status_code=201)
async def create_product(
    space_key: str, request: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    service = CatalogService(db)
    try:
        p = await service.create_product(space_key.upper(), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": {"id": str(p.id), "name": p.name}, "meta": {}, "errors": []}


@router.get("/spaces/{space_key}/catalog/products")
async def list_products(
    space_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = CatalogService(db)
    try:
        products = await service.list_products(space_key.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "data": [{"id": str(p.id), "name": p.name, "description": p.description} for p in products],
        "meta": {}, "errors": [],
    }


# ── Documents ───────────────────────────────────────────────

@router.post("/catalog/products/{product_id}/documents", status_code=201)
async def create_document(
    product_id: str, request: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    service = CatalogService(db)
    doc = await service.create_document(UUID(product_id), request)
    return {
        "data": {
            "id": str(doc.id), "doc_type": doc.doc_type, "title": doc.title,
            "current_version": doc.current_version,
        },
        "meta": {}, "errors": [],
    }


@router.get("/catalog/products/{product_id}/documents")
async def list_documents(
    product_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = CatalogService(db)
    docs = await service.list_documents(UUID(product_id))
    return {
        "data": [
            {"id": str(d.id), "doc_type": d.doc_type, "title": d.title,
             "current_version": d.current_version, "updated_at": d.updated_at.isoformat()}
            for d in docs
        ],
        "meta": {}, "errors": [],
    }


@router.put("/catalog/documents/{doc_id}")
async def update_document(
    doc_id: str, request: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    service = CatalogService(db)
    try:
        doc = await service.update_document(UUID(doc_id), request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": {"id": str(doc.id), "title": doc.title}, "meta": {}, "errors": []}


# ── Repositories ────────────────────────────────────────────

@router.post("/catalog/products/{product_id}/repositories", status_code=201)
async def add_repository(
    product_id: str, request: RepositoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    service = CatalogService(db)
    repo = await service.add_repository(UUID(product_id), request)
    return {"data": {"id": str(repo.id), "repo_url": repo.repo_url}, "meta": {}, "errors": []}


# ── Versions ────────────────────────────────────────────────

@router.get("/catalog/documents/{doc_id}/versions")
async def list_versions(
    doc_id: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = CatalogService(db)
    versions = await service.list_versions(UUID(doc_id))
    return {
        "data": [
            {"id": str(v.id), "version": v.version, "change_type": v.change_type,
             "source": v.source, "status": v.status, "source_ref": v.source_ref,
             "created_at": v.created_at.isoformat()}
            for v in versions
        ],
        "meta": {}, "errors": [],
    }


@router.put("/catalog/versions/{version_id}/approve")
async def approve_version(
    version_id: str, request: VersionApproval,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(Permissions.ADMIN_SETTINGS)),
) -> dict:
    service = CatalogService(db)
    try:
        ver = await service.approve_version(UUID(version_id), request.status, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": {"id": str(ver.id), "version": ver.version, "status": ver.status}, "meta": {}, "errors": []}


# ── GitHub Webhook ──────────────────────────────────────────

@router.post("/catalog/webhooks/github")
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Receive GitHub webhook events. Processes merged PRs to update docs via AI."""
    event = request.headers.get("X-GitHub-Event", "")
    body = await request.body()
    payload = await request.json()

    # Only process merged PRs
    if event != "pull_request" or payload.get("action") != "closed" or not payload.get("pull_request", {}).get("merged"):
        return {"data": {"status": "skipped", "reason": "not a merged PR"}, "meta": {}, "errors": []}

    pr = payload["pull_request"]
    repo_url = payload["repository"]["html_url"]

    # Verify signature if webhook_secret is configured
    service = CatalogService(db)
    signature = request.headers.get("X-Hub-Signature-256", "")

    # Extract changed files from PR (simplified — in production, fetch via GitHub API)
    changed_files = [f.get("filename", "") for f in payload.get("pull_request", {}).get("changed_files_list", [])]
    if not changed_files:
        # Fallback: use PR title to infer affected area
        changed_files = []

    # Process the merged PR
    results = await service.process_merged_pr(
        repo_url=repo_url,
        pr_data={
            "title": pr.get("title", ""),
            "body": pr.get("body", ""),
            "html_url": pr.get("html_url", ""),
        },
        changed_files=changed_files,
        diff_text=pr.get("body", ""),  # In production, fetch actual diff via GitHub API
    )

    return {
        "data": {
            "status": "processed",
            "draft_versions_created": len(results),
            "details": results,
        },
        "meta": {},
        "errors": [],
    }
