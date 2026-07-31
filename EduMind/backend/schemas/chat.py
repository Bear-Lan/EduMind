"""
EduMind Chat Schemas

Pydantic validation models for AI tutoring dialogue inputs and responses.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Validation schema for sending questions to the AI Coach."""

    message: str = Field(..., min_length=1)


class ChatReference(BaseModel):
    """Reference document schema returned alongside AI answers."""

    title: str
    topic: str
    source: str | None


class ChatResponse(BaseModel):
    """Dialogue response schema returned by the AI Coach."""

    session_id: int
    response: str
    references: list[ChatReference] = []


class ChatHistoryItem(BaseModel):
    """Validation schema representing a single logged dialog record."""

    id: int
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
