"""Add student account status and forced password change flags.

Revision ID: b71c9e4d2f06
Revises: a8d4f2c91b30
Create Date: 2026-08-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b71c9e4d2f06"
down_revision: Union[str, None] = "a8d4f2c91b30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "students",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("students", "must_change_password")
    op.drop_column("students", "is_active")
