"""widen market quote integer fields

Revision ID: 20260427_0003
Revises: 20260426_0002
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260427_0003"
down_revision: str | None = "20260426_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("market_quotes") as batch_op:
        batch_op.alter_column(
            "volume",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "market_cap",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("market_quotes") as batch_op:
        batch_op.alter_column(
            "market_cap",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "volume",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
