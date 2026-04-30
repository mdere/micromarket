from datetime import datetime

from pydantic import BaseModel, Field


class ArticleInput(BaseModel):
    title: str | None = None
    source: str | None = None
    url: str | None = None
    text: str | None = None
    published_at: datetime | None = None


class AnalysisCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    primary_horizon: str = "3_trading_days"
    analysis_as_of: datetime | None = None
    articles: list[ArticleInput] = Field(default_factory=list)


class ArticleEntityResponse(BaseModel):
    id: str
    entity_type: str
    name: str
    symbol: str | None = None
    canonical_name: str
    relationship_type: str
    confidence_score: str
    evidence_snippets: list[str] = Field(default_factory=list)
    provider: str
    model_name: str
    model_version: str


class ArticleResponse(BaseModel):
    id: str
    title: str | None
    source: str | None
    url: str | None
    published_at: str | None = None
    input_type: str
    content_hash: str
    word_count: int
    raw_artifact_path: str | None
    relevance_score: str | None = None
    duplicate_group_id: str | None = None
    included_in_forecast: bool = True
    exclusion_reason: str | None = None
    entities: list[ArticleEntityResponse] = Field(default_factory=list)


class TrackingNeedResponse(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    name: str
    symbol: str | None = None
    canonical_name: str
    suggested_symbol: str | None = None
    tracking_type: str
    reason: str
    evidence_snippets: list[str] = Field(default_factory=list)
    priority_score: str
    status: str
    provider: str
    model_name: str
    model_version: str


class TrackingNeedUpdate(BaseModel):
    status: str


class MarketQuoteResponse(BaseModel):
    id: str
    provider: str
    price: str | None
    previous_close: str | None
    open: str | None
    day_high: str | None
    day_low: str | None
    volume: int | None
    market_cap: int | None
    quote_time: str | None
    retrieved_at: str


class TickerContextResponse(BaseModel):
    provider: str
    lookback_days: int
    history_start_date: str | None
    history_end_date: str | None
    stored_price_count: int


class SentimentRunResponse(BaseModel):
    id: str
    article_id: str
    provider: str
    model_name: str
    model_version: str
    sentiment_label: str
    sentiment_score: str
    confidence_score: str
    drivers: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SentimentAggregateResponse(BaseModel):
    article_count: int
    included_article_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    mixed_count: int
    aggregate_score: str | None
    agreement_score: str | None
    evidence_strength_score: str | None
    summary: str | None


class ForecastRunResponse(BaseModel):
    id: str
    horizon: str
    provider: str
    model_name: str
    model_version: str
    predicted_direction: str
    predicted_percent_change: str | None
    confidence_score: str
    baseline_direction: str | None
    baseline_percent_change: str | None
    feature_snapshot: dict = Field(default_factory=dict)
    top_factors: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    target_start_price: str | None
    target_start_time: str | None
    target_end_time: str | None
    feature_window_start_time: str | None = None
    feature_window_end_time: str | None = None


class AnalysisResponse(BaseModel):
    id: str
    ticker: str
    status: str
    primary_horizon: str
    input_mode: str = "manual_text"
    analysis_as_of: str | None = None
    analysis_as_of_source: str = "live"
    created_at: str
    completed_at: str | None = None
    error_message: str | None = None
    message: str
    limitations: list[str] = Field(default_factory=list)
    articles: list[ArticleResponse] = Field(default_factory=list)
    market_quote: MarketQuoteResponse | None = None
    ticker_context: TickerContextResponse | None = None
    sentiment_runs: list[SentimentRunResponse] = Field(default_factory=list)
    sentiment_aggregate: SentimentAggregateResponse | None = None
    forecast_runs: list[ForecastRunResponse] = Field(default_factory=list)
    tracking_needs: list[TrackingNeedResponse] = Field(default_factory=list)
