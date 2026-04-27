from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.session import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    asset_type: Mapped[str] = mapped_column(String(32), default="equity")
    exchange: Mapped[str | None] = mapped_column(String(64))
    sector: Mapped[str | None] = mapped_column(String(128))
    industry: Mapped[str | None] = mapped_column(String(128))
    currency: Mapped[str | None] = mapped_column(String(8), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="asset")
    articles: Mapped[list["Article"]] = relationship(back_populates="asset")


class MarketQuote(Base):
    __tablename__ = "market_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    analysis_id: Mapped[str | None] = mapped_column(ForeignKey("analyses.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    previous_close: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    open: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    day_high: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    day_low: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    market_cap: Mapped[int | None] = mapped_column(BigInteger)
    fifty_two_week_high: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    fifty_two_week_low: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    moving_average_50: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    moving_average_200: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    beta: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    quote_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    raw_payload_artifact_path: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped["Analysis | None"] = relationship(back_populates="market_quotes")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    primary_horizon: Mapped[str] = mapped_column(String(32), default="3_trading_days")
    input_mode: Mapped[str] = mapped_column(String(32), default="manual_text")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)

    asset: Mapped[Asset] = relationship(back_populates="analyses")
    analysis_articles: Mapped[list["AnalysisArticle"]] = relationship(back_populates="analysis")
    articles: Mapped[list["Article"]] = relationship(
        secondary="analysis_articles", viewonly=True, back_populates="analyses"
    )
    market_quotes: Mapped[list[MarketQuote]] = relationship(back_populates="analysis")
    sentiment_runs: Mapped[list["SentimentRun"]] = relationship(back_populates="analysis")
    sentiment_aggregate: Mapped["SentimentAggregate | None"] = relationship(
        back_populates="analysis", uselist=False
    )
    forecast_runs: Mapped[list["ForecastRun"]] = relationship(back_populates="analysis")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str | None] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_type: Mapped[str] = mapped_column(String(32), default="manual_text")
    raw_artifact_path: Mapped[str | None] = mapped_column(Text)
    extracted_text_artifact_path: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), default="en")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset: Mapped[Asset] = relationship(back_populates="articles")
    analysis_articles: Mapped[list["AnalysisArticle"]] = relationship(back_populates="article")
    analyses: Mapped[list[Analysis]] = relationship(
        secondary="analysis_articles", viewonly=True, back_populates="articles"
    )
    sentiment_runs: Mapped[list["SentimentRun"]] = relationship(back_populates="article")


class AnalysisArticle(Base):
    __tablename__ = "analysis_articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    duplicate_group_id: Mapped[str | None] = mapped_column(String(64))
    included_in_forecast: Mapped[bool] = mapped_column(Boolean, default=True)
    exclusion_reason: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[Analysis] = relationship(back_populates="analysis_articles")
    article: Mapped[Article] = relationship(back_populates="analysis_articles")


class SentimentRun(Base):
    __tablename__ = "sentiment_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128))
    model_version: Mapped[str] = mapped_column(String(64))
    sentiment_label: Mapped[str] = mapped_column(String(32))
    sentiment_score: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    drivers: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_snippets: Mapped[list[str]] = mapped_column(JSON, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw_output_artifact_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    analysis: Mapped[Analysis] = relationship(back_populates="sentiment_runs")
    article: Mapped[Article] = relationship(back_populates="sentiment_runs")


class SentimentAggregate(Base):
    __tablename__ = "sentiment_aggregates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), unique=True, index=True)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    included_article_count: Mapped[int] = mapped_column(Integer, default=0)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)
    mixed_count: Mapped[int] = mapped_column(Integer, default=0)
    aggregate_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    agreement_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    evidence_strength_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    analysis: Mapped[Analysis] = relationship(back_populates="sentiment_aggregate")


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    horizon: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128))
    model_version: Mapped[str] = mapped_column(String(64))
    predicted_direction: Mapped[str] = mapped_column(String(32))
    predicted_percent_change: Mapped[Decimal | None] = mapped_column(Numeric(8, 5))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    baseline_direction: Mapped[str | None] = mapped_column(String(32))
    baseline_percent_change: Mapped[Decimal | None] = mapped_column(Numeric(8, 5))
    feature_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    top_factors: Mapped[list[str]] = mapped_column(JSON, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    target_start_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    target_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    target_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    analysis: Mapped[Analysis] = relationship(back_populates="forecast_runs")


class ForecastOutcome(Base):
    __tablename__ = "forecast_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    forecast_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_runs.id"), unique=True)
    actual_end_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    actual_percent_change: Mapped[Decimal | None] = mapped_column(Numeric(8, 5))
    actual_direction: Mapped[str | None] = mapped_column(String(32))
    direction_correct: Mapped[bool | None] = mapped_column(Boolean)
    absolute_error: Mapped[Decimal | None] = mapped_column(Numeric(8, 5))
    baseline_direction_correct: Mapped[bool | None] = mapped_column(Boolean)
    baseline_absolute_error: Mapped[Decimal | None] = mapped_column(Numeric(8, 5))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_type: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(64))
    artifact_path: Mapped[str | None] = mapped_column(Text)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    notes: Mapped[str | None] = mapped_column(Text)


class ProviderCall(Base):
    __tablename__ = "provider_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str | None] = mapped_column(ForeignKey("analyses.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    operation: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
