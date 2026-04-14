"""API v1 router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.spaces import router as spaces_router
from app.api.v1.items import router as items_router
from app.api.v1.board import router as board_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.custom_fields import router as custom_fields_router
from app.api.v1.wiki import router as wiki_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(spaces_router)
router.include_router(items_router)
router.include_router(board_router)
router.include_router(workflows_router)
router.include_router(custom_fields_router)
router.include_router(wiki_router)
