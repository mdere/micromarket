"""add analysis tracking needs

Revision ID: 20260430_0006
Revises: 20260428_0005
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260430_0006"
down_revision: str | None = "20260428_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_tracking_needs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("primary_asset_id", sa.String(length=36), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("suggested_symbol", sa.String(length=32), nullable=True),
        sa.Column("tracking_type", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_snippets", sa.JSON(), nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"]),
        sa.ForeignKeyConstraint(["primary_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_id",
            "entity_id",
            "tracking_type",
            name="uq_analysis_tracking_needs_type",
        ),
    )
    op.create_index(
        op.f("ix_analysis_tracking_needs_analysis_id"),
        "analysis_tracking_needs",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analysis_tracking_needs_entity_id"),
        "analysis_tracking_needs",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analysis_tracking_needs_primary_asset_id"),
        "analysis_tracking_needs",
        ["primary_asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analysis_tracking_needs_suggested_symbol"),
        "analysis_tracking_needs",
        ["suggested_symbol"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_analysis_tracking_needs_suggested_symbol"),
        table_name="analysis_tracking_needs",
    )
    op.drop_index(
        op.f("ix_analysis_tracking_needs_primary_asset_id"),
        table_name="analysis_tracking_needs",
    )
    op.drop_index(
        op.f("ix_analysis_tracking_needs_entity_id"),
        table_name="analysis_tracking_needs",
    )
    op.drop_index(
        op.f("ix_analysis_tracking_needs_analysis_id"),
        table_name="analysis_tracking_needs",
    )
    op.drop_table("analysis_tracking_needs")
