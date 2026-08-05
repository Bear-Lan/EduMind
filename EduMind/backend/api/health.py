"""
EduMind Health Check API

GET /api/v1/health

Returns the status of all system components.
No business logic. No authentication required.
"""

import logging
from fastapi import APIRouter
from schemas.response import StandardResponse
from config.settings import settings
from services.model_config import model_config_service

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("", response_model=StandardResponse)
async def health_check() -> StandardResponse:
    """
    Check the health status of all EduMind system components.

    Returns status for: API, Database, Vector DB, LLM service.
    """
    logger.info("Health check requested")

    # Component status checks (stubs for Phase 1)
    db_status = await _check_database()
    qdrant_status = await _check_qdrant()
    llm_status = await _check_llm()

    all_healthy = all([db_status, qdrant_status, llm_status])

    return StandardResponse.ok(
        data={
            "api": "ok",
            "database": "ok" if db_status else "unavailable",
            "vector_db": "ok" if qdrant_status else "unavailable",
            "llm": "ok" if llm_status else "unavailable",
            "environment": settings.app_env,
        },
        message="healthy" if all_healthy else "degraded",
    )


async def _check_database() -> bool:
    """Verify PostgreSQL connectivity."""
    try:
        from database.connection import engine
        if engine is None:
            return False
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return False


async def _check_qdrant() -> bool:
    """Verify Qdrant connectivity by reusing the shared RAG module client."""
    try:
        from rag import rag_module
        # Reuse the existing singleton client (avoids file-lock conflicts in disk mode)
        client = rag_module.get_client()
        await client.get_collections()
        return True
    except Exception as exc:
        logger.warning(f"Qdrant health check failed: {exc}")
        return False


async def _check_llm() -> bool:
    """Verify DeepSeek API key is configured (not actual call)."""
    return bool(model_config_service.runtime.llm_api_key)
