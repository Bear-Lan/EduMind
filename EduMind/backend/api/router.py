"""
EduMind Central API Router

Registers all sub-routers under /api/v1.
No business logic permitted here.
"""

from fastapi import APIRouter
from api.health import router as health_router
from api.auth import router as auth_router
from api.profile import router as profile_router
from api.assessment import router as assessment_router
from api.plan import router as plan_router
from api.chat import router as chat_router
from api.learning import router as learning_router
from api.resources import router as resources_router
from api.knowledge_graph import router as kg_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(assessment_router)
api_router.include_router(plan_router)
api_router.include_router(chat_router)
api_router.include_router(learning_router)
api_router.include_router(resources_router)
api_router.include_router(kg_router)
