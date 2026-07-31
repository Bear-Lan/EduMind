"""
EduMind Dependency Injection

FastAPI dependency providers.
Provides async DB sessions and extracts active student from JWT tokens.
"""

from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from database.connection import get_db_session
from models.student import Student
from core.exceptions import UnauthorizedError

# oauth2_scheme points to the login route for Swagger integration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session per request."""
    async for session in get_db_session():
        yield session


async def get_current_student(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Student:
    """
    Dependency to authenticate request and return the active Student ORM entity.

    Decodes JWT token, extracts student_id from 'sub' claim.
    Raises UnauthorizedError if token is invalid or user does not exist.
    """
    secret_key = settings.jwt_secret_key or "default_secret_key_for_testing"
    try:
        payload = jwt.decode(
            token, secret_key, algorithms=[settings.jwt_algorithm]
        )
        student_id_str: str | None = payload.get("sub")
        if student_id_str is None:
            raise UnauthorizedError("Invalid token claims")
        student_id = int(student_id_str)
    except (JWTError, ValueError):
        raise UnauthorizedError("Could not validate credentials")

    student = await db.get(Student, student_id)
    if student is None:
        raise UnauthorizedError("User does not exist")

    return student
