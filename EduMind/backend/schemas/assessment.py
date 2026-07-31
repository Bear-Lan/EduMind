"""
EduMind Assessment Schemas

Pydantic validation models for submitting score evaluations.
"""

from pydantic import BaseModel, Field


class AssessmentSubmitRequest(BaseModel):
    """Validation schema for submitting assessment scores."""

    topic: str = Field(..., min_length=1, max_length=255)
    score: float = Field(..., ge=0.0, le=1.0)  # Decimal score between 0.0 and 1.0
    duration: int = Field(0, ge=0)  # Duration spent in seconds

class AssessmentGradeRequest(BaseModel):
    """Validation schema for grading an assessment answer."""
    topic: str = Field(...)
    question: str = Field(...)
    answer: str = Field(...)

