"""Administrator and encrypted model configuration database models."""

import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class AdminUser(Base):
    """Privileged account used only for system administration."""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False, default="系统管理员")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class SystemModelConfig(Base):
    """Single-row, encrypted configuration for external AI services."""

    __tablename__ = "system_model_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    llm_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(255), nullable=False)
    llm_max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=4096)
    llm_temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    llm_enable_thinking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    llm_timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=60.0)

    embedding_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False, default=1024)

    updated_by: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
