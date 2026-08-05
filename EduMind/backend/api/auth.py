"""
EduMind Authentication API

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_student, get_db
from core.security import hash_password, verify_password, create_access_token
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
    StudentAccountResponse,
    StudentAccountUpdateRequest,
    StudentPasswordChangeRequest,
    TokenResponse,
)
from schemas.response import StandardResponse
from student_profile import student_profile_service
from models.student import Student
from core.exceptions import UnauthorizedError, ValidationError

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
    token = create_access_token(data={"sub": str(student.id), "role": "student"})
    await db.commit()
    return StandardResponse.created(
        data=TokenResponse(access_token=token, must_change_password=False),
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
    if not student.is_active:
        raise UnauthorizedError("该学生账户已被停用，请联系管理员")

    # Issue access token
    token = create_access_token(data={"sub": str(student.id), "role": "student"})
    return StandardResponse.ok(
        data=TokenResponse(
            access_token=token,
            must_change_password=student.must_change_password,
        ),
        message="Login successful",
    )


@router.get("/account", response_model=StandardResponse[StudentAccountResponse])
async def get_account(
    current_student: Student = Depends(get_current_student),
) -> StandardResponse[StudentAccountResponse]:
    """Return the logged-in student's editable account information."""
    return StandardResponse.ok(data=StudentAccountResponse.model_validate(current_student))


@router.put("/account", response_model=StandardResponse[StudentAccountResponse])
async def update_account(
    payload: StudentAccountUpdateRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[StudentAccountResponse]:
    """Update student identity and learning-related account fields."""
    username = payload.username.strip()
    if username != current_student.username:
        existing_id = await db.scalar(select(Student.id).where(Student.username == username))
        if existing_id:
            raise ValidationError("该用户名已被使用")
        current_student.username = username

    current_student.name = payload.name.strip()
    current_student.grade = payload.grade.strip() if payload.grade else None
    current_student.subject = payload.subject.strip() if payload.subject else None
    current_student.target_score = payload.target_score
    await db.flush()
    return StandardResponse.ok(
        data=StudentAccountResponse.model_validate(current_student),
        message="账户资料已更新",
    )


@router.put("/password", response_model=StandardResponse)
async def change_student_password(
    payload: StudentPasswordChangeRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Change the logged-in student's password after verifying the old password."""
    if not verify_password(payload.current_password, current_student.hashed_password):
        raise UnauthorizedError("当前密码不正确")
    current_student.hashed_password = hash_password(payload.new_password)
    current_student.must_change_password = False
    await db.flush()
    return StandardResponse.ok(message="登录密码已更新")


@router.post("/logout", response_model=StandardResponse)
async def logout() -> StandardResponse:
    """Stateless logout (client should discard token)."""
    return StandardResponse.ok(message="Logout successful")
