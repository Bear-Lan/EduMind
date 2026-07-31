"""
EduMind Student Profile Schemas

Pydantic validation models for student profile reading and updating.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    """Validation schema for student profile update payload."""

    current_goal: str | None = Field(None, max_length=255)
    subject: str | None = Field(None, max_length=50)
    learning_preferences: dict | None = Field(None)


class ProfileResponse(BaseModel):
    """Validation schema for student profile response details."""

    id: int
    student_id: int
    subject: str | None
    current_goal: str | None
    mastery_map: dict | None
    learning_preferences: dict | None
    last_recommendation: dict | None
    updated_at: datetime

    class Config:
        from_attributes = True
