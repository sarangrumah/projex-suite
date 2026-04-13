---
name: fastapi-backend
description: FastAPI backend development patterns for ProjeX Suite. Use when creating API endpoints, services, models, schemas, or middleware. Covers multi-tenant patterns, RBAC, Pydantic v2, SQLAlchemy async.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# FastAPI Backend Patterns

## API Endpoint Template

```python
# app/api/v1/{module}.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_permission
from app.models.user import User
from app.schemas.{module} import CreateRequest, UpdateRequest, Response
from app.services.{module}_service import {Module}Service

router = APIRouter(prefix="/{module}s", tags=["{module}s"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
@require_permission("{module}:create")
async def create(
    request: CreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = {Module}Service(db)
    item = await service.create(request, current_user)
    return {"data": item, "meta": {}, "errors": []}

@router.get("/", response_model=dict)
async def list_all(
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = {Module}Service(db)
    items, total = await service.list(page, per_page)
    return {
        "data": items,
        "meta": {"page": page, "per_page": per_page, "total": total},
        "errors": [],
    }
```

## Pydantic v2 Schema Template

```python
# app/schemas/{module}.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime

class CreateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str = Field(..., min_length=1, max_length=255)

class Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    created_at: datetime
```

## SQLAlchemy Model Template

```python
# app/models/{module}.py
from sqlalchemy import Column, String, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class {Model}(Base):
    __tablename__ = "{table_name}"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    # ALWAYS include tenant context via schema-per-tenant search_path
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
```

## Service Layer Template

```python
# app/services/{module}_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.{module} import {Model}

class {Module}Service:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data, current_user):
        item = {Model}(**data.model_dump(), created_by=current_user.id)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list(self, page: int, per_page: int):
        offset = (page - 1) * per_page
        query = select({Model}).offset(offset).limit(per_page)
        result = await self.db.execute(query)
        items = result.scalars().all()
        count_q = select(func.count()).select_from({Model})
        total = (await self.db.execute(count_q)).scalar()
        return items, total
```

## CRITICAL RULES
- NEVER write raw SQL — use SQLAlchemy ORM
- NEVER skip tenant_id filtering — middleware handles via search_path
- ALWAYS use Pydantic v2 with `model_config = ConfigDict(strict=True)`
- ALWAYS add type hints to all function parameters and return values
- ALWAYS put business logic in services/, not in route handlers
- ALWAYS return `{"data": ..., "meta": ..., "errors": []}` envelope
