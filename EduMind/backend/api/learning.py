"""
EduMind Learning Progress API

POST /api/v1/learning/complete
GET /api/v1/learning/progress
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.learning import StepCompleteRequest
from schemas.response import StandardResponse
from models.student import Student
from models.history import LearningHistory
from application.orchestrator import orchestrator
from student_profile import student_profile_service

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post("/complete", response_model=StandardResponse)
async def submit_learning_completion(
    payload: StepCompleteRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Record completion of a single study step item in a learning plan."""
    res = await orchestrator.handle_learning_completion(
        db=db,
        student_id=current_student.id,
        completion_data={
            "plan_id": payload.plan_id,
            "step_number": payload.step_number,
            "score": payload.score,
            "duration": payload.duration,
        },
    )
    await db.commit()
    return StandardResponse.ok(
        data=res,
        message="Learning step completion registered successfully",
    )


@router.get("/progress", response_model=StandardResponse)
async def get_overall_progress(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Retrieve aggregate learning statistics (mastery map and study steps count)."""
    profile = await student_profile_service.get_profile(db, current_student.id)

    completions_count = await db.scalar(
        select(func.count(LearningHistory.id)).where(
            LearningHistory.student_id == current_student.id,
            LearningHistory.activity_type == "learning_completion",
        )
    )

    return StandardResponse.ok(
        data={
            "mastery_map": profile.mastery_map or {},
            "completions_count": completions_count or 0,
        },
        message="Learning progress metrics retrieved successfully",
    )
