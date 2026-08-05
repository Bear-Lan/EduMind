"""Schemas for administrator authentication and model configuration."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, model_validator


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class AdminSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "admin"
    username: str
    display_name: str
    must_change_password: bool


class AdminPasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=12, max_length=100)

    @model_validator(mode="after")
    def passwords_must_differ(self) -> "AdminPasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        return self


class AdminStudentResponse(BaseModel):
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


class AdminStudentListResponse(BaseModel):
    items: list[AdminStudentResponse]
    total: int
    page: int
    page_size: int


class AdminStudentUpdateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    grade: str | None = Field(None, max_length=50)
    subject: str | None = Field(None, max_length=50)
    target_score: float | None = Field(None, ge=0.0, le=100.0)


class AdminStudentStatusRequest(BaseModel):
    is_active: bool


class AdminStudentPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=100)


class ModelConfigResponse(BaseModel):
    llm_api_key_configured: bool
    llm_api_key_masked: str
    llm_base_url: str
    llm_model: str
    llm_max_tokens: int
    llm_temperature: float
    llm_enable_thinking: bool
    llm_timeout_seconds: float
    embedding_api_key_configured: bool
    embedding_api_key_masked: str
    embedding_base_url: str
    embedding_model: str
    embedding_dimensions: int
    updated_at: datetime | None = None


class ModelConfigUpdateRequest(BaseModel):
    llm_api_key: str | None = Field(None, max_length=500)
    clear_llm_api_key: bool = False
    llm_base_url: HttpUrl
    llm_model: str = Field(..., min_length=1, max_length=255)
    llm_max_tokens: int = Field(4096, ge=128, le=32768)
    llm_temperature: float = Field(0.3, ge=0.0, le=2.0)
    llm_enable_thinking: bool = False
    llm_timeout_seconds: float = Field(60.0, ge=5.0, le=300.0)

    embedding_api_key: str | None = Field(None, max_length=500)
    clear_embedding_api_key: bool = False
    embedding_base_url: HttpUrl
    embedding_model: str = Field(..., min_length=1, max_length=255)
    embedding_dimensions: int = Field(1024, ge=64, le=8192)


class ModelConnectionTestRequest(BaseModel):
    service: str = Field(..., pattern="^(llm|embedding)$")
    api_key: str | None = Field(None, max_length=500)
    base_url: HttpUrl
    model: str = Field(..., min_length=1, max_length=255)
    embedding_dimensions: int | None = Field(None, ge=64, le=8192)


class ModelConnectionTestResponse(BaseModel):
    service: str
    connected: bool
    model: str
    detail: str
    dimensions: int | None = None
