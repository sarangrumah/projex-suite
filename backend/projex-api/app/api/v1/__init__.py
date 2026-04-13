"""API v1 router — aggregates all endpoint modules."""

from fastapi import APIRouter

router = APIRouter()

# Endpoint modules will be included here as they are built:
# from app.api.v1 import auth, spaces, items, board, workflows
# router.include_router(auth.router)
# router.include_router(spaces.router)
# router.include_router(items.router)
# router.include_router(board.router)
# router.include_router(workflows.router)
