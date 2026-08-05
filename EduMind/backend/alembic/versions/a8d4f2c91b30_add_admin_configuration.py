"""Add administrator and encrypted model configuration tables.

Revision ID: a8d4f2c91b30
Revises: ee7a7031b86f
Create Date: 2026-08-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8d4f2c91b30"
down_revision: Union[str, None] = "ee7a7031b86f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_users_username"), "admin_users", ["username"], unique=True)

    op.create_table(
        "system_model_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("llm_api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("llm_base_url", sa.String(length=500), nullable=False),
        sa.Column("llm_model", sa.String(length=255), nullable=False),
        sa.Column("llm_max_tokens", sa.Integer(), nullable=False),
        sa.Column("llm_temperature", sa.Float(), nullable=False),
        sa.Column("llm_enable_thinking", sa.Boolean(), nullable=False),
        sa.Column("llm_timeout_seconds", sa.Float(), nullable=False),
        sa.Column("embedding_api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("embedding_base_url", sa.String(length=500), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["admin_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("system_model_config")
    op.drop_index(op.f("ix_admin_users_username"), table_name="admin_users")
    op.drop_table("admin_users")
