"""
EduMind Authentication Schemas

Pydantic validation models for user registration, login, and JWT token exchange.
"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Validation schema for student registration payload."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    grade: str | None = Field(None, max_length=50)
    subject: str | None = Field(None, max_length=50)
    target_score: float | None = Field(None, ge=0.0)


class LoginRequest(BaseModel):
    """Validation schema for credentials login payload."""

    username: str = Field(...)
    password: str = Field(...)


class TokenResponse(BaseModel):
    """Validation schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
