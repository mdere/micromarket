from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ForecastResult:
    horizon: str
    predicted_direction: str
    predicted_percent_change: float | None
    confidence: float
    baseline_direction: str | None = None
    baseline_percent_change: float | None = None
    feature_snapshot: dict = field(default_factory=dict)
    top_factors: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    provider: str = "baseline"
    model_name: str = "forecast-rules"
    model_version: str = "0.1.0"
    target_start_price: Decimal | None = None
    target_start_time: datetime | None = None
    target_end_time: datetime | None = None
    feature_window_start_time: datetime | None = None
    feature_window_end_time: datetime | None = None


@dataclass(frozen=True)
class ForecastInput:
    ticker: str
    quote_provider: str | None
    current_price: Decimal | None
    previous_close: Decimal | None
    quote_time: datetime | None
    sentiment_score: Decimal | None
    agreement_score: Decimal | None
    evidence_strength_score: Decimal | None
    article_count: int
    included_article_count: int
    analysis_as_of: datetime | None = None
    feature_window_start_time: datetime | None = None
    feature_window_end_time: datetime | None = None
    market_lookback_days: int | None = None
    stored_price_count: int | None = None


class ForecastProvider(Protocol):
    def generate_forecasts(self, forecast_input: ForecastInput) -> list[ForecastResult]:
        """Generate forecast results for the MVP horizons."""
