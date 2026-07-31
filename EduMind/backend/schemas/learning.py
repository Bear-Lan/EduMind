"""
EduMind Learning Progress Schemas

Pydantic validation models for task step completions.
"""

from pydantic import BaseModel, Field


class StepCompleteRequest(BaseModel):
    """Validation schema for completing a specific study plan step."""

    plan_id: int = Field(...)
    step_number: int = Field(...)
    score: float = Field(1.0, ge=0.0, le=1.0)  # Decimal score between 0.0 and 1.0
    duration: int = Field(0, ge=0)  # Spent duration in seconds
