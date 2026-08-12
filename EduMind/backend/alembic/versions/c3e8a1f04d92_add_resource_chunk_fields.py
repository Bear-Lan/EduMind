"""Add chunk lineage columns to learning_resources.

Revision ID: c3e8a1f04d92
Revises: b71c9e4d2f06
Create Date: 2026-08-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3e8a1f04d92"
down_revision: Union[str, None] = "b71c9e4d2f06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "learning_resources",
        sa.Column("parent_doc", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "learning_resources",
        sa.Column("chapter", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "learning_resources",
        sa.Column("section", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "learning_resources",
        sa.Column("chunk_index", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index(
        "ix_learning_resources_parent_doc",
        "learning_resources",
        ["parent_doc"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_learning_resources_parent_doc", table_name="learning_resources")
    op.drop_column("learning_resources", "chunk_index")
    op.drop_column("learning_resources", "section")
    op.drop_column("learning_resources", "chapter")
    op.drop_column("learning_resources", "parent_doc")
