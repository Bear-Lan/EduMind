"""
EduMind Application Configuration

Loads all configuration from environment variables.
No hardcoded values are permitted in this file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator

# Locate the project root .env file dynamically
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"

    # PostgreSQL / SQLite
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "edumind"
    postgres_user: str = "edumind_user"
    postgres_password: str = ""
    database_url: str = ""

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        """Auto-resolve DATABASE_URL and relative QDRANT_PATH."""
        project_root = Path(__file__).resolve().parent.parent.parent
        # Resolve DATABASE_URL
        if not self.database_url:
            data_dir = project_root / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "edumind.db"
            self.database_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
        # Resolve relative QDRANT_PATH (e.g. ./data/qdrant_storage)
        if self.qdrant_path and self.qdrant_path != ":memory:" and self.qdrant_path.startswith("."):
            resolved = (project_root / self.qdrant_path).resolve()
            resolved.mkdir(parents=True, exist_ok=True)
            self.qdrant_path = str(resolved)
        return self

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_path: str | None = None
    qdrant_collection_name: str = "edumind_resources"

    # RAG retrieval quality gate
    rag_score_threshold: float = 0.35  # cosine similarity below this is dropped; empty -> refusal

    # Embeddings (OpenAI-compatible)
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 384

    # DeepSeek LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_tokens: int = 4096
    deepseek_temperature: float = 0.7
    deepseek_enable_thinking: bool = False
    deepseek_timeout_seconds: float = 60.0

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # First-run administrator bootstrap. The password is only used when the
    # administrator table is empty; afterwards the database hash is authoritative.
    admin_bootstrap_username: str = "edumind_admin"
    admin_bootstrap_password: str = ""

    @property
    def jwt_signing_key(self) -> str:
        """Return the single key used for both JWT signing and verification."""
        return self.jwt_secret_key or "default_secret_key_for_testing"

    # CORS
    cors_origins: str = "http://localhost:5173"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    def get_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
