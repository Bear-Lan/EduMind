"""Administrator-only student account management endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_admin, get_db
from core.exceptions import NotFoundError, ValidationError
from core.security import hash_password
from models.admin import AdminUser
from models.student import Student
from schemas.admin import (
    AdminStudentListResponse,
    AdminStudentPasswordResetRequest,
    AdminStudentResponse,
    AdminStudentStatusRequest,
    AdminStudentUpdateRequest,
)
from schemas.response import StandardResponse

router = APIRouter(prefix="/admin/students", tags=["admin-students"])


async def _student_or_error(db: AsyncSession, student_id: int) -> Student:
    student = await db.get(Student, student_id)
    if student is None:
        raise NotFoundError("Student", str(student_id))
    return student


@router.get("", response_model=StandardResponse[AdminStudentListResponse])
async def list_students(
    search: str = Query("", max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AdminStudentListResponse]:
    """List and search students without exposing password hashes."""
    del admin
    keyword = search.strip()
    count_stmt = select(func.count(Student.id))
    list_stmt = select(Student).order_by(Student.created_at.desc(), Student.id.desc())
    if keyword:
        pattern = f"%{keyword}%"
        condition = or_(Student.username.ilike(pattern), Student.name.ilike(pattern))
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = int(await db.scalar(count_stmt) or 0)
    students = list(
        (await db.scalars(list_stmt.offset((page - 1) * page_size).limit(page_size))).all()
    )
    return StandardResponse.ok(
        data=AdminStudentListResponse(
            items=[AdminStudentResponse.model_validate(student) for student in students],
            total=total,
            page=page,
            page_size=page_size,
        ),
        message="学生账户读取成功",
    )


@router.put("/{student_id}", response_model=StandardResponse[AdminStudentResponse])
async def update_student(
    student_id: int,
    payload: AdminStudentUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AdminStudentResponse]:
    """Update a student's basic account fields."""
    del admin
    student = await _student_or_error(db, student_id)
    username = payload.username.strip()
    if username != student.username:
        existing_id = await db.scalar(select(Student.id).where(Student.username == username))
        if existing_id:
            raise ValidationError("该用户名已被使用")
        student.username = username
    student.name = payload.name.strip()
    student.grade = payload.grade.strip() if payload.grade else None
    student.subject = payload.subject.strip() if payload.subject else None
    student.target_score = payload.target_score
    await db.flush()
    return StandardResponse.ok(
        data=AdminStudentResponse.model_validate(student),
        message="学生账户资料已更新",
    )


@router.put("/{student_id}/status", response_model=StandardResponse[AdminStudentResponse])
async def update_student_status(
    student_id: int,
    payload: AdminStudentStatusRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AdminStudentResponse]:
    """Enable or disable a student; disabled tokens stop working immediately."""
    del admin
    student = await _student_or_error(db, student_id)
    student.is_active = payload.is_active
    await db.flush()
    state = "启用" if payload.is_active else "停用"
    return StandardResponse.ok(
        data=AdminStudentResponse.model_validate(student),
        message=f"学生账户已{state}",
    )


@router.put("/{student_id}/password", response_model=StandardResponse)
async def reset_student_password(
    student_id: int,
    payload: AdminStudentPasswordResetRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Set a temporary password and require the student to change it after login."""
    del admin
    student = await _student_or_error(db, student_id)
    student.hashed_password = hash_password(payload.new_password)
    student.must_change_password = True
    await db.flush()
    return StandardResponse.ok(message="学生临时密码已重置，登录后将提示修改")
