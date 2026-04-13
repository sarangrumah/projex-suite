"""API v1 router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router)

# Future endpoint modules:
# from app.api.v1 import spaces, items, board, workflows
# router.include_router(spaces.router)
# router.include_router(items.router)
# router.include_router(board.router)
# router.include_router(workflows.router)
