"""
EduMind Student Profile API

GET /api/v1/profile
PUT /api/v1/profile
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.profile import ProfileUpdateRequest, ProfileResponse
from schemas.response import StandardResponse
from models.student import Student
from student_profile import student_profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=StandardResponse[ProfileResponse])
async def get_profile(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProfileResponse]:
    """Retrieve the logged-in student's profile settings and mastery maps."""
    profile = await student_profile_service.get_profile(db, current_student.id)
    profile_dict = profile.__dict__.copy()
    profile_dict["subject"] = current_student.subject
    return StandardResponse.ok(
        data=profile_dict,
        message="Profile retrieved successfully",
    )


@router.put("", response_model=StandardResponse[ProfileResponse])
async def update_profile(
    payload: ProfileUpdateRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProfileResponse]:
    """Update student's goal, subject, and/or learning preferences."""
    profile = await student_profile_service.update_profile(
        db=db,
        student_id=current_student.id,
        goal=payload.current_goal,
        subject=payload.subject,
        preferences=payload.learning_preferences,
        runtime_api_key="",
    )
    await db.commit()
    profile_dict = profile.__dict__.copy()
    profile_dict["subject"] = payload.subject or current_student.subject
    return StandardResponse.ok(
        data=profile_dict,
        message="Profile updated successfully",
    )
