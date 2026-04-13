"""API v1 router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.spaces import router as spaces_router
from app.api.v1.items import router as items_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(spaces_router)
router.include_router(items_router)

# Future endpoint modules:
# from app.api.v1 import board, workflows
# router.include_router(board.router)
# router.include_router(workflows.router)
