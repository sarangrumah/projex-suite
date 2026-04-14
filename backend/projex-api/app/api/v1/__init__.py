"""API v1 router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.spaces import router as spaces_router
from app.api.v1.items import router as items_router
from app.api.v1.board import router as board_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.custom_fields import router as custom_fields_router
from app.api.v1.wiki import router as wiki_router
from app.api.v1.budgets import router as budgets_router
from app.api.v1.goals import router as goals_router
from app.api.v1.dashboards import router as dashboards_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.search import router as search_router
from app.api.v1.sprints import router as sprints_router
from app.api.v1.users import router as users_router
from app.api.v1.system import router as system_router
from app.api.v1.files import router as files_router
from app.api.v1.links import router as links_router
from app.api.v1.era_ai import router as era_ai_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(spaces_router)
router.include_router(items_router)
router.include_router(board_router)
router.include_router(workflows_router)
router.include_router(custom_fields_router)
router.include_router(wiki_router)
router.include_router(budgets_router)
router.include_router(goals_router)
router.include_router(dashboards_router)
router.include_router(catalog_router)
router.include_router(notifications_router)
router.include_router(search_router)
router.include_router(sprints_router)
router.include_router(users_router)
router.include_router(system_router)
router.include_router(files_router)
router.include_router(links_router)
router.include_router(era_ai_router)
