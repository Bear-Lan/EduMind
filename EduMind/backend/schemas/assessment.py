"""
EduMind Assessment Schemas

Pydantic validation models for assessment endpoints.
"""

from pydantic import BaseModel, Field


class AssessmentSubmitRequest(BaseModel):
    """旧兼容接口：直接提交分数。"""

    topic: str = Field(..., min_length=1, max_length=255)
    score: float = Field(..., ge=0.0, le=1.0)
    duration: int = Field(0, ge=0)


class AssessmentGradeRequest(BaseModel):
    """旧接口（fallback）：LLM 评语。"""

    topic: str = Field(...)
    question: str = Field(...)
    answer: str = Field(...)


class QuizSubmitRequest(BaseModel):
    """新接口：提交题库作答。"""

    question_id: int = Field(..., ge=1)
    user_answer: dict = Field(...)
    duration: int = Field(0, ge=0)
    runtime_api_key: str = Field("", max_length=512)