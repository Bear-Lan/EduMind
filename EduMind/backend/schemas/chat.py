"""
EduMind Chat Schemas

Pydantic validation models for AI tutoring dialogue inputs and responses.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Validation schema for sending questions to the AI Coach."""

    message: str = Field(..., min_length=1)
    mode: str = Field(
        "normal",
        description="Coaching mode: 'normal' (heuristic) or 'socratic' (guided questioning)",
    )


class ChatReference(BaseModel):
    """Reference document schema returned alongside AI answers."""

    id: int | None = None
    title: str
    topic: str
    subject: str | None = None
    source: str | None = None
    parent_doc: str | None = None
    chapter: str | None = None
    section: str | None = None
    chunk_index: int | None = None
    score: float | None = Field(
        None,
        description="Fused retrieval relevance in [0,1] (vector + keyword + rerank), not raw cosine",
    )
    snippet: str | None = Field(None, description="Short excerpt for citation preview")
    content: str | None = Field(
        None,
        description="Textbook segment for expand view (may be truncated for payload size)",
    )


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
