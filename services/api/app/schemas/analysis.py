from pydantic import BaseModel, Field


class ArticleInput(BaseModel):
    title: str | None = None
    source: str | None = None
    url: str | None = None
    text: str | None = None


class AnalysisCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    primary_horizon: str = "3_trading_days"
    articles: list[ArticleInput] = Field(default_factory=list)


class ArticleResponse(BaseModel):
    id: str
    title: str | None
    source: str | None
    url: str | None
    input_type: str
    content_hash: str
    word_count: int
    raw_artifact_path: str | None


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


class AnalysisResponse(BaseModel):
    id: str
    ticker: str
    status: str
    primary_horizon: str
    input_mode: str = "manual_text"
    message: str
    limitations: list[str] = Field(default_factory=list)
    articles: list[ArticleResponse] = Field(default_factory=list)
    market_quote: MarketQuoteResponse | None = None
    sentiment_runs: list[SentimentRunResponse] = Field(default_factory=list)
    sentiment_aggregate: SentimentAggregateResponse | None = None
