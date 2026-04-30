"""link tracking needs to onboarded assets

Revision ID: 20260430_0007
Revises: 20260430_0006
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260430_0007"
down_revision: str | None = "20260430_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_tracking_needs") as batch_op:
        batch_op.add_column(sa.Column("related_asset_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_analysis_tracking_needs_related_asset_id_assets",
            "assets",
            ["related_asset_id"],
            ["id"],
        )
    op.create_index(
        op.f("ix_analysis_tracking_needs_related_asset_id"),
        "analysis_tracking_needs",
        ["related_asset_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_analysis_tracking_needs_related_asset_id"),
        table_name="analysis_tracking_needs",
    )
    with op.batch_alter_table("analysis_tracking_needs") as batch_op:
        batch_op.drop_constraint(
            "fk_analysis_tracking_needs_related_asset_id_assets",
            type_="foreignkey",
        )
        batch_op.drop_column("related_asset_id")
