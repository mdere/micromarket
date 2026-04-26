"""link market quotes to analyses

Revision ID: 20260426_0002
Revises: 20260426_0001
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260426_0002"
down_revision: str | None = "20260426_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("market_quotes") as batch_op:
        batch_op.add_column(sa.Column("analysis_id", sa.String(length=36), nullable=True))
        batch_op.create_index(
            op.f("ix_market_quotes_analysis_id"),
            ["analysis_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_market_quotes_analysis_id_analyses",
            "analyses",
            ["analysis_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("market_quotes") as batch_op:
        batch_op.drop_constraint("fk_market_quotes_analysis_id_analyses", type_="foreignkey")
        batch_op.drop_index(op.f("ix_market_quotes_analysis_id"))
        batch_op.drop_column("analysis_id")
