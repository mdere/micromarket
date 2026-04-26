"""initial MVP schema

Revision ID: 20260426_0001
Revises:
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260426_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index(op.f("ix_assets_symbol"), "assets", ["symbol"], unique=False)

    op.create_table(
        "analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("primary_horizon", sa.String(length=32), nullable=False),
        sa.Column("input_mode", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analyses_asset_id"), "analyses", ["asset_id"], unique=False)

    op.create_table(
        "articles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_type", sa.String(length=32), nullable=False),
        sa.Column("raw_artifact_path", sa.Text(), nullable=True),
        sa.Column("extracted_text_artifact_path", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_articles_asset_id"), "articles", ["asset_id"], unique=False)
    op.create_index(op.f("ix_articles_content_hash"), "articles", ["content_hash"], unique=False)

    op.create_table(
        "market_quotes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("previous_close", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("open", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("day_high", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("day_low", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("market_cap", sa.Integer(), nullable=True),
        sa.Column("fifty_two_week_high", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("fifty_two_week_low", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("moving_average_50", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("moving_average_200", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("beta", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("pe_ratio", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("quote_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload_artifact_path", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_quotes_asset_id"), "market_quotes", ["asset_id"], unique=False)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "analysis_articles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("article_id", sa.String(length=36), nullable=False),
        sa.Column("relevance_score", sa.Numeric(precision=6, scale=5), nullable=True),
        sa.Column("duplicate_group_id", sa.String(length=64), nullable=True),
        sa.Column("included_in_forecast", sa.Boolean(), nullable=False),
        sa.Column("exclusion_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_analysis_articles_analysis_id"),
        "analysis_articles",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analysis_articles_article_id"),
        "analysis_articles",
        ["article_id"],
        unique=False,
    )

    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("horizon", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("predicted_direction", sa.String(length=32), nullable=False),
        sa.Column("predicted_percent_change", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("confidence_score", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("baseline_direction", sa.String(length=32), nullable=True),
        sa.Column("baseline_percent_change", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("feature_snapshot", sa.JSON(), nullable=False),
        sa.Column("top_factors", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_start_price", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("target_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_forecast_runs_analysis_id"),
        "forecast_runs",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(op.f("ix_forecast_runs_asset_id"), "forecast_runs", ["asset_id"], unique=False)

    op.create_table(
        "provider_calls",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_provider_calls_analysis_id"),
        "provider_calls",
        ["analysis_id"],
        unique=False,
    )

    op.create_table(
        "sentiment_aggregates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("article_count", sa.Integer(), nullable=False),
        sa.Column("included_article_count", sa.Integer(), nullable=False),
        sa.Column("positive_count", sa.Integer(), nullable=False),
        sa.Column("neutral_count", sa.Integer(), nullable=False),
        sa.Column("negative_count", sa.Integer(), nullable=False),
        sa.Column("mixed_count", sa.Integer(), nullable=False),
        sa.Column("aggregate_score", sa.Numeric(precision=6, scale=5), nullable=True),
        sa.Column("agreement_score", sa.Numeric(precision=6, scale=5), nullable=True),
        sa.Column("evidence_strength_score", sa.Numeric(precision=6, scale=5), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id"),
    )
    op.create_index(
        op.f("ix_sentiment_aggregates_analysis_id"),
        "sentiment_aggregates",
        ["analysis_id"],
        unique=False,
    )

    op.create_table(
        "sentiment_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("article_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("sentiment_label", sa.String(length=32), nullable=False),
        sa.Column("sentiment_score", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("drivers", sa.JSON(), nullable=False),
        sa.Column("evidence_snippets", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("raw_output_artifact_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sentiment_runs_analysis_id"),
        "sentiment_runs",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sentiment_runs_article_id"),
        "sentiment_runs",
        ["article_id"],
        unique=False,
    )

    op.create_table(
        "forecast_outcomes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("forecast_run_id", sa.String(length=36), nullable=False),
        sa.Column("actual_end_price", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("actual_percent_change", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("actual_direction", sa.String(length=32), nullable=True),
        sa.Column("direction_correct", sa.Boolean(), nullable=True),
        sa.Column("absolute_error", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("baseline_direction_correct", sa.Boolean(), nullable=True),
        sa.Column("baseline_absolute_error", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["forecast_run_id"], ["forecast_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("forecast_run_id"),
    )


def downgrade() -> None:
    op.drop_table("forecast_outcomes")
    op.drop_index(op.f("ix_sentiment_runs_article_id"), table_name="sentiment_runs")
    op.drop_index(op.f("ix_sentiment_runs_analysis_id"), table_name="sentiment_runs")
    op.drop_table("sentiment_runs")
    op.drop_index(op.f("ix_sentiment_aggregates_analysis_id"), table_name="sentiment_aggregates")
    op.drop_table("sentiment_aggregates")
    op.drop_index(op.f("ix_provider_calls_analysis_id"), table_name="provider_calls")
    op.drop_table("provider_calls")
    op.drop_index(op.f("ix_forecast_runs_asset_id"), table_name="forecast_runs")
    op.drop_index(op.f("ix_forecast_runs_analysis_id"), table_name="forecast_runs")
    op.drop_table("forecast_runs")
    op.drop_index(op.f("ix_analysis_articles_article_id"), table_name="analysis_articles")
    op.drop_index(op.f("ix_analysis_articles_analysis_id"), table_name="analysis_articles")
    op.drop_table("analysis_articles")
    op.drop_table("model_versions")
    op.drop_index(op.f("ix_market_quotes_asset_id"), table_name="market_quotes")
    op.drop_table("market_quotes")
    op.drop_index(op.f("ix_articles_content_hash"), table_name="articles")
    op.drop_index(op.f("ix_articles_asset_id"), table_name="articles")
    op.drop_table("articles")
    op.drop_index(op.f("ix_analyses_asset_id"), table_name="analyses")
    op.drop_table("analyses")
    op.drop_index(op.f("ix_assets_symbol"), table_name="assets")
    op.drop_table("assets")
