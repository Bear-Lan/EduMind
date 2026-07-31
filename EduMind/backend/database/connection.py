"""
EduMind Database Connection

Manages PostgreSQL async connection and session lifecycle.
No business logic is permitted here.
"""

from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from config.settings import settings

logger = logging.getLogger(__name__)

engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker | None = None


def create_engine() -> AsyncEngine:
    """Create the async SQLAlchemy engine."""
    kwargs = {
        "echo": settings.is_development,
        "pool_pre_ping": True,
    }
    # Only PostgreSQL supports connection pool sizing (SQLite uses NullPool by default)
    if settings.database_url.startswith("postgresql"):
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20

    return create_async_engine(
        settings.database_url,
        **kwargs
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    """Create the async session factory."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def init_db() -> None:
    """Initialize database connection on application startup."""
    global engine, async_session_factory
    try:
        engine = create_engine()
        async_session_factory = create_session_factory(engine)
        # Verify connectivity
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("Database connection established")

        # Auto-create all ORM tables (safe for SQLite dev; no-op if tables already exist)
        from database.base import Base
        import models  # noqa: F401 – triggers registration of all ORM models via __init__.py
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified / created")
    except Exception as exc:
        logger.warning(f"Database not available at startup: {exc}")


async def close_db() -> None:
    """Close database connection on application shutdown."""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for use in request handlers."""
    if async_session_factory is None:
        raise RuntimeError("Database not initialized")
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
