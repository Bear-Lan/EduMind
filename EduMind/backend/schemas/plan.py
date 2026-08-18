"""
EduMind Learning Plan Schemas

Pydantic validation models for structured study plans.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PlanStep(BaseModel):
    """Validation schema representing a single study step checklist item."""

    step_number: int
    title: str
    description: str
    completed: bool


class PlanResponse(BaseModel):
    """Validation schema for learning plan responses."""

    id: int
    target_topic: str
    learning_steps: list[PlanStep] = []
    recommendation_reason: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
