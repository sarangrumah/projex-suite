"""File upload API — upload/download attachments via MinIO."""

from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models.file import File
from uuid import UUID

router = APIRouter(tags=["files"])

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp",
                 "application/pdf", "text/plain", "text/csv",
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/items/{item_key}/files", status_code=201)
async def upload_file(
    item_key: str,
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type '{file.content_type}' not allowed")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Get work item
    from app.models.work_item import WorkItem
    result = await db.execute(select(WorkItem).where(WorkItem.key == item_key.upper()))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    storage_key = f"items/{item.id}/{uuid.uuid4()}/{file.filename}"

    # Upload to MinIO
    try:
        from minio import Minio
        from io import BytesIO
        client = Minio(settings.minio_endpoint, access_key=settings.minio_access_key,
                       secret_key=settings.minio_secret_key, secure=settings.minio_secure)
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
        client.put_object(settings.minio_bucket, storage_key, BytesIO(content), len(content),
                         content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {e}")

    file_record = File(
        work_item_id=item.id, uploaded_by=UUID(current_user["sub"]),
        filename=file.filename or "unnamed", content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content), storage_key=storage_key,
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    return {
        "data": {"id": str(file_record.id), "filename": file_record.filename,
                 "size_bytes": file_record.size_bytes, "content_type": file_record.content_type},
        "meta": {}, "errors": [],
    }


@router.get("/items/{item_key}/files")
async def list_files(
    item_key: str, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    from app.models.work_item import WorkItem
    result = await db.execute(select(WorkItem).where(WorkItem.key == item_key.upper()))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    files_result = await db.execute(select(File).where(File.work_item_id == item.id))
    files = list(files_result.scalars().all())
    return {
        "data": [
            {"id": str(f.id), "filename": f.filename, "content_type": f.content_type,
             "size_bytes": f.size_bytes, "created_at": f.created_at.isoformat()}
            for f in files
        ],
        "meta": {}, "errors": [],
    }
