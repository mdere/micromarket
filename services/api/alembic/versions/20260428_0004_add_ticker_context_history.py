"""add ticker context and market history

Revision ID: 20260428_0004
Revises: 20260427_0003
Create Date: 2026-04-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260428_0004"
down_revision: str | None = "20260427_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_price_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("high", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("low", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("close", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("adjusted_close", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload_artifact_path", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "provider", "price_date", name="uq_market_history_day"),
    )
    op.create_index(
        op.f("ix_market_price_history_asset_id"),
        "market_price_history",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_market_price_history_price_date"),
        "market_price_history",
        ["price_date"],
        unique=False,
    )

    op.create_table(
        "ticker_contexts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("lookback_days", sa.Integer(), nullable=False),
        sa.Column("history_start_date", sa.Date(), nullable=True),
        sa.Column("history_end_date", sa.Date(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("last_backfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id", "provider", "lookback_days", name="uq_ticker_context_provider_window"
        ),
    )
    op.create_index(
        op.f("ix_ticker_contexts_asset_id"),
        "ticker_contexts",
        ["asset_id"],
        unique=False,
    )

    with op.batch_alter_table("analyses") as batch_op:
        batch_op.add_column(sa.Column("analysis_as_of", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column("analysis_as_of_source", sa.String(length=32), nullable=False, server_default="live")
        )
    with op.batch_alter_table("forecast_runs") as batch_op:
        batch_op.add_column(
            sa.Column("feature_window_start_time", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("feature_window_end_time", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("forecast_runs") as batch_op:
        batch_op.drop_column("feature_window_end_time")
        batch_op.drop_column("feature_window_start_time")
    with op.batch_alter_table("analyses") as batch_op:
        batch_op.drop_column("analysis_as_of_source")
        batch_op.drop_column("analysis_as_of")

    op.drop_index(op.f("ix_ticker_contexts_asset_id"), table_name="ticker_contexts")
    op.drop_table("ticker_contexts")
    op.drop_index(op.f("ix_market_price_history_price_date"), table_name="market_price_history")
    op.drop_index(op.f("ix_market_price_history_asset_id"), table_name="market_price_history")
    op.drop_table("market_price_history")
