"""
EduMind Application Entry Point

Responsibilities:
- Start FastAPI application
- Register all API routers
- Configure CORS
- Configure exception handlers
- Manage startup and shutdown lifecycle

No business logic is permitted in this file.
"""

import sys
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

# Must import settings and logging before anything else
from config.settings import settings
from core.logging import setup_logging
from core.exceptions import EduMindException
from api.router import api_router
from api.analytics import router as analytics_router
from database.connection import init_db, close_db

# Initialize logging immediately
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    logger.info("=" * 50)
    logger.info("EduMind V1 starting up")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Host: {settings.app_host}:{settings.app_port}")
    logger.info("=" * 50)

    await init_db()
    logger.info("EduMind V1 ready")

    yield

    # Shutdown
    logger.info("EduMind V1 shutting down")
    await close_db()
    logger.info("EduMind V1 stopped")


# Create FastAPI application
app = FastAPI(
    title="EduMind V1",
    description="AI-powered Personalized Learning Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for EduMind errors
@app.exception_handler(EduMindException)
async def edumind_exception_handler(
    request: Request, exc: EduMindException
) -> JSONResponse:
    logger.error(f"EduMindException: {exc.message} (code={exc.code})")
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=exc.code,
        headers={"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"},
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "data": None,
        },
    )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=500,
        headers={"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"},
        content={
            "success": False,
            "code": 500,
            "message": f"Internal server error: {str(exc)}",
            "data": None,
        },
    )


# Register all API routes
app.include_router(api_router)
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/client", response_class=FileResponse)
async def client_app():
    """Serve the interactive HTML test client."""
    client_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_client.html")
    return FileResponse(client_path)


@app.get("/")
async def root():
    """Root endpoint — redirects to API docs."""
    return {"message": "EduMind V1 API", "docs": "/docs", "health": "/api/v1/health"}
