"""Encrypted persistent model configuration with a process-local runtime cache."""

import base64
import hashlib
import logging
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from core.security import hash_password
from models.admin import AdminUser, SystemModelConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeModelConfig:
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_max_tokens: int
    llm_temperature: float
    llm_enable_thinking: bool
    llm_timeout_seconds: float
    embedding_api_key: str
    embedding_base_url: str
    embedding_model: str
    embedding_dimensions: int


def _settings_fallback() -> RuntimeModelConfig:
    return RuntimeModelConfig(
        llm_api_key=settings.deepseek_api_key,
        llm_base_url=settings.deepseek_base_url,
        llm_model=settings.deepseek_model,
        llm_max_tokens=settings.deepseek_max_tokens,
        llm_temperature=settings.deepseek_temperature,
        llm_enable_thinking=settings.deepseek_enable_thinking,
        llm_timeout_seconds=settings.deepseek_timeout_seconds,
        embedding_api_key=settings.embedding_api_key,
        embedding_base_url=settings.embedding_base_url,
        embedding_model=settings.embedding_model,
        embedding_dimensions=settings.embedding_dimensions,
    )


class ModelConfigService:
    """Owns encrypted storage and exposes non-async reads to model clients."""

    def __init__(self) -> None:
        self._runtime = _settings_fallback()
        digest = hashlib.sha256(settings.jwt_signing_key.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    @property
    def runtime(self) -> RuntimeModelConfig:
        return self._runtime

    def reset_to_environment(self) -> None:
        """Refresh the cache from Settings (used by isolated tests and recovery paths)."""
        self._runtime = _settings_fallback()

    def encrypt(self, value: str) -> str | None:
        value = value.strip()
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii") if value else None

    def decrypt(self, value: str | None) -> str:
        if not value:
            return ""
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken:
            logger.error("Stored model secret cannot be decrypted; falling back to an empty key")
            return ""

    @staticmethod
    def mask(value: str) -> str:
        if not value:
            return "未配置"
        if len(value) <= 8:
            return "••••••••"
        return f"{value[:3]}••••••{value[-4:]}"

    async def bootstrap(self, db: AsyncSession) -> None:
        """Create the first admin and migrate environment model settings into encrypted storage."""
        admin = await db.scalar(select(AdminUser).where(AdminUser.username == settings.admin_bootstrap_username))
        if admin is None:
            if settings.admin_bootstrap_password:
                admin = AdminUser(
                    username=settings.admin_bootstrap_username,
                    hashed_password=hash_password(settings.admin_bootstrap_password),
                    display_name="EduMind 系统管理员",
                    must_change_password=True,
                )
                db.add(admin)
                await db.flush()
                logger.info("Bootstrap administrator created: %s", settings.admin_bootstrap_username)
            else:
                logger.warning(
                    "⚠️  Admin table is empty but ADMIN_BOOTSTRAP_PASSWORD is not set. "
                    "Set it in .env to create the first administrator account."
                )

        row = await db.get(SystemModelConfig, 1)
        if row is None:
            fallback = _settings_fallback()
            row = SystemModelConfig(
                id=1,
                llm_api_key_encrypted=self.encrypt(fallback.llm_api_key),
                llm_base_url=fallback.llm_base_url,
                llm_model=fallback.llm_model,
                llm_max_tokens=fallback.llm_max_tokens,
                llm_temperature=fallback.llm_temperature,
                llm_enable_thinking=fallback.llm_enable_thinking,
                llm_timeout_seconds=fallback.llm_timeout_seconds,
                embedding_api_key_encrypted=self.encrypt(fallback.embedding_api_key),
                embedding_base_url=fallback.embedding_base_url,
                embedding_model=fallback.embedding_model,
                embedding_dimensions=fallback.embedding_dimensions,
                updated_by=admin.id if admin else None,
            )
            db.add(row)
            await db.flush()

        self._apply_row(row)

    async def load(self, db: AsyncSession) -> SystemModelConfig | None:
        row = await db.get(SystemModelConfig, 1)
        if row:
            self._apply_row(row)
        return row

    def _apply_row(self, row: SystemModelConfig) -> None:
        self._runtime = RuntimeModelConfig(
            llm_api_key=self.decrypt(row.llm_api_key_encrypted),
            llm_base_url=row.llm_base_url,
            llm_model=row.llm_model,
            llm_max_tokens=row.llm_max_tokens,
            llm_temperature=row.llm_temperature,
            llm_enable_thinking=row.llm_enable_thinking,
            llm_timeout_seconds=row.llm_timeout_seconds,
            embedding_api_key=self.decrypt(row.embedding_api_key_encrypted),
            embedding_base_url=row.embedding_base_url,
            embedding_model=row.embedding_model,
            embedding_dimensions=row.embedding_dimensions,
        )


model_config_service = ModelConfigService()


async def bootstrap_admin_and_model_config() -> None:
    """Run startup initialization after database tables have been created."""
    from database.connection import get_db_session

    async for db in get_db_session():
        await model_config_service.bootstrap(db)
        await db.commit()
        break
