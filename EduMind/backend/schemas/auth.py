"""
EduMind Authentication Schemas

Pydantic validation models for user registration, login, and JWT token exchange.
"""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class RegisterRequest(BaseModel):
    """Validation schema for student registration payload."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
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
    role: str = "student"
    must_change_password: bool = False


class StudentAccountResponse(BaseModel):
    id: int
    username: str
    name: str
    grade: str | None
    subject: str | None
    target_score: float | None
    is_active: bool
    must_change_password: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StudentAccountUpdateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    grade: str | None = Field(None, max_length=50)
    subject: str | None = Field(None, max_length=50)
    target_score: float | None = Field(None, ge=0.0, le=100.0)


class StudentPasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)

    @model_validator(mode="after")
    def passwords_must_differ(self) -> "StudentPasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        return self
