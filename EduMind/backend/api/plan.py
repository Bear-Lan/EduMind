"""
EduMind Learning Plan API

POST /api/v1/plan/generate
GET /api/v1/plan/current
"""

from fastapi import APIRouter, Depends, Header
from typing import Optional
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.response import StandardResponse
from models.student import Student
from models.plan import LearningPlan
from application.orchestrator import orchestrator

router = APIRouter(prefix="/plan", tags=["plan"])


@router.post("/generate", response_model=StandardResponse)
async def generate_plan(
    target_topic: Optional[str] = None,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> StandardResponse:
    """Abandon current active plans and force-generate a fresh study recommendation."""
    # Mark old active plans as abandoned
    await db.execute(
        update(LearningPlan)
        .where(
            LearningPlan.student_id == current_student.id,
            LearningPlan.status == "active",
        )
        .values(status="abandoned")
    )
    await db.flush()

    res = await orchestrator.handle_learning_plan(
        db, current_student.id, runtime_api_key=x_api_key or "", force_topic=target_topic
    )
    await db.commit()
    return StandardResponse.ok(
        data=res,
        message="New learning plan generated successfully",
    )


@router.get("/current", response_model=StandardResponse)
async def get_current_plan(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> StandardResponse:
    """Retrieve the current active learning plan (or auto-generates if none exists)."""
    res = await orchestrator.handle_learning_plan(
        db, current_student.id, runtime_api_key=x_api_key or ""
    )
    await db.commit()
    return StandardResponse.ok(
        data=res,
        message="Current active learning plan retrieved successfully",
    )
