"""
EduMind Assessment API

POST /api/v1/assessment
GET /api/v1/assessment/result
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.assessment import AssessmentSubmitRequest, AssessmentGradeRequest
from schemas.response import StandardResponse
from models.student import Student
from application.orchestrator import orchestrator
from student_profile import student_profile_service
from llm import llm_service
from typing import Optional
from fastapi import Header

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.post("", response_model=StandardResponse)
async def submit_assessment(
    payload: AssessmentSubmitRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Submit a finished quiz or test score and trigger recommendations."""
    res = await orchestrator.handle_assessment(
        db=db,
        student_id=current_student.id,
        assessment_data={
            "topic": payload.topic,
            "score": payload.score,
            "duration": payload.duration,
        },
    )
    await db.commit()
    return StandardResponse.ok(
        data=res,
        message="Assessment submitted and profile updated successfully",
    )


@router.get("/result", response_model=StandardResponse)
async def get_latest_result(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Retrieve the student's current mastery mapping details."""
    profile = await student_profile_service.get_profile(db, current_student.id)
    return StandardResponse.ok(
        data={"mastery_map": profile.mastery_map or {}},
        message="Assessment results retrieved successfully",
    )

@router.get("/generate", response_model=StandardResponse)
async def generate_quiz_for_topic(
    topic: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> StandardResponse:
    """Generate a quiz question for the specified topic."""
    question = await llm_service.generate_quiz(topic=topic, runtime_api_key=x_api_key or "")
    return StandardResponse.ok(
        data={"question": question},
        message="Quiz generated successfully",
    )

@router.post("/grade", response_model=StandardResponse)
async def grade_quiz_answer(
    payload: AssessmentGradeRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> StandardResponse:
    """Grade a student's answer and return a score and feedback."""
    result = await llm_service.grade_answer(
        topic=payload.topic, 
        question=payload.question, 
        answer=payload.answer,
        runtime_api_key=x_api_key or ""
    )
    return StandardResponse.ok(
        data=result,
        message="Answer graded successfully",
    )

