"""
EduMind Authentication API

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import hash_password, verify_password, create_access_token
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from schemas.response import StandardResponse
from student_profile import student_profile_service
from models.student import Student
from core.exceptions import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=StandardResponse[TokenResponse])
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> StandardResponse[TokenResponse]:
    """Register a new student and return a JWT access token."""
    # Hash password
    hashed = hash_password(payload.password)

    # Create student and profile
    student = await student_profile_service.create_student(
        db=db,
        username=payload.username,
        hashed_password=hashed,
        name=payload.name,
        grade=payload.grade,
        subject=payload.subject,
        target_score=payload.target_score,
    )

    # Issue access token
    token = create_access_token(data={"sub": str(student.id)})
    await db.commit()
    return StandardResponse.created(
        data=TokenResponse(access_token=token),
        message="Registration successful",
    )


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(
    payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> StandardResponse[TokenResponse]:
    """Authenticate a student user and return a JWT access token."""
    # Query student record
    student = await db.scalar(
        select(Student).where(Student.username == payload.username)
    )
    if not student or not verify_password(payload.password, student.hashed_password):
        raise UnauthorizedError("Incorrect username or password")

    # Issue access token
    token = create_access_token(data={"sub": str(student.id)})
    return StandardResponse.ok(
        data=TokenResponse(access_token=token),
        message="Login successful",
    )


@router.post("/logout", response_model=StandardResponse)
async def logout() -> StandardResponse:
    """Stateless logout (client should discard token)."""
    return StandardResponse.ok(message="Logout successful")
