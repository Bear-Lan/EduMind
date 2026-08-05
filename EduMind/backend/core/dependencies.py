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
from models.admin import AdminUser
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
    try:
        payload = jwt.decode(
            token, settings.jwt_signing_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("role", "student") != "student":
            raise UnauthorizedError("Student credentials required")
        student_id_str: str | None = payload.get("sub")
        if student_id_str is None:
            raise UnauthorizedError("Invalid token claims")
        student_id = int(student_id_str)
    except (JWTError, ValueError):
        raise UnauthorizedError("Could not validate credentials")

    student = await db.get(Student, student_id)
    if student is None:
        raise UnauthorizedError("User does not exist")
    if not student.is_active:
        raise UnauthorizedError("该学生账户已被停用，请联系管理员")

    return student


async def get_current_admin(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> AdminUser:
    """Authenticate an administrator JWT and return the active admin account."""
    try:
        payload = jwt.decode(
            token, settings.jwt_signing_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("role") != "admin":
            raise UnauthorizedError("Administrator credentials required")
        admin_id_str: str | None = payload.get("sub")
        if admin_id_str is None:
            raise UnauthorizedError("Invalid administrator token claims")
        admin_id = int(admin_id_str)
    except (JWTError, ValueError):
        raise UnauthorizedError("Could not validate administrator credentials")

    admin = await db.get(AdminUser, admin_id)
    if admin is None or not admin.is_active:
        raise UnauthorizedError("Administrator account is unavailable")
    return admin
