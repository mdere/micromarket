from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.forecasting.provider import ForecastInput, ForecastResult


class BaselineForecastProvider:
    provider_name = "baseline"
    model_name = "forecast-rule-baseline"
    model_version = "0.1.0"
    horizons = ("next_close", "3_trading_days", "7_trading_days")

    _horizon_scales = {
        "next_close": Decimal("0.35"),
        "3_trading_days": Decimal("0.75"),
        "7_trading_days": Decimal("1.10"),
    }

    def generate_forecasts(self, forecast_input: ForecastInput) -> list[ForecastResult]:
        return [self._forecast_horizon(forecast_input, horizon) for horizon in self.horizons]

    def _forecast_horizon(self, forecast_input: ForecastInput, horizon: str) -> ForecastResult:
        sentiment_score = forecast_input.sentiment_score or Decimal("0")
        evidence_strength = forecast_input.evidence_strength_score or Decimal("0")
        agreement = forecast_input.agreement_score or Decimal("0")
        momentum = self._momentum_percent(forecast_input)
        scale = self._horizon_scales[horizon]

        sentiment_component = sentiment_score * scale
        momentum_component = (momentum or Decimal("0")) * Decimal("0.20")
        predicted_percent_change = sentiment_component + momentum_component

        confidence = self._confidence(
            predicted_percent_change=predicted_percent_change,
            evidence_strength=evidence_strength,
            agreement=agreement,
            included_article_count=forecast_input.included_article_count,
        )
        predicted_direction = self._direction(predicted_percent_change, confidence)
        limitations = self._limitations(forecast_input, momentum)
        top_factors = self._top_factors(sentiment_score, evidence_strength, agreement, momentum)

        return ForecastResult(
            horizon=horizon,
            predicted_direction=predicted_direction,
            predicted_percent_change=round(float(predicted_percent_change), 5),
            confidence=round(float(confidence), 5),
            baseline_direction="flat",
            baseline_percent_change=0.0,
            feature_snapshot={
                "ticker": forecast_input.ticker,
                "quote_provider": forecast_input.quote_provider,
                "analysis_as_of": self._datetime_to_str(forecast_input.analysis_as_of),
                "feature_window_start_time": self._datetime_to_str(
                    forecast_input.feature_window_start_time
                ),
                "feature_window_end_time": self._datetime_to_str(
                    forecast_input.feature_window_end_time
                ),
                "market_lookback_days": forecast_input.market_lookback_days,
                "stored_price_count": forecast_input.stored_price_count,
                "current_price": self._decimal_to_str(forecast_input.current_price),
                "previous_close": self._decimal_to_str(forecast_input.previous_close),
                "sentiment_score": self._decimal_to_str(forecast_input.sentiment_score),
                "agreement_score": self._decimal_to_str(forecast_input.agreement_score),
                "evidence_strength_score": self._decimal_to_str(
                    forecast_input.evidence_strength_score
                ),
                "article_count": forecast_input.article_count,
                "included_article_count": forecast_input.included_article_count,
                "momentum_percent": self._decimal_to_str(momentum),
            },
            top_factors=top_factors,
            limitations=limitations,
            provider=self.provider_name,
            model_name=self.model_name,
            model_version=self.model_version,
            target_start_price=forecast_input.current_price,
            target_start_time=forecast_input.analysis_as_of or forecast_input.quote_time,
            target_end_time=self._target_end_time(
                forecast_input.analysis_as_of or forecast_input.quote_time, horizon
            ),
            feature_window_start_time=forecast_input.feature_window_start_time,
            feature_window_end_time=forecast_input.feature_window_end_time,
        )

    def _momentum_percent(self, forecast_input: ForecastInput) -> Decimal | None:
        if (
            forecast_input.current_price is None
            or forecast_input.previous_close is None
            or forecast_input.previous_close == Decimal("0")
        ):
            return None
        return (
            (forecast_input.current_price - forecast_input.previous_close)
            / forecast_input.previous_close
            * Decimal("100")
        )

    def _confidence(
        self,
        predicted_percent_change: Decimal,
        evidence_strength: Decimal,
        agreement: Decimal,
        included_article_count: int,
    ) -> Decimal:
        signal_strength = min(abs(predicted_percent_change) / Decimal("2"), Decimal("0.15"))
        confidence = (
            Decimal("0.20")
            + evidence_strength * Decimal("0.25")
            + agreement * Decimal("0.20")
            + signal_strength
        )
        if included_article_count < 2:
            confidence -= Decimal("0.10")
        return min(max(confidence, Decimal("0.05")), Decimal("0.75"))

    def _direction(self, predicted_percent_change: Decimal, confidence: Decimal) -> str:
        if abs(predicted_percent_change) < Decimal("0.10") or confidence < Decimal("0.35"):
            return "uncertain"
        if predicted_percent_change > Decimal("0"):
            return "up"
        return "down"

    def _limitations(self, forecast_input: ForecastInput, momentum: Decimal | None) -> list[str]:
        limitations = [
            "Research-only forecast; not financial advice.",
            "Rule-based baseline has not yet been evaluated against outcomes.",
        ]
        if forecast_input.included_article_count < 3:
            limitations.append("Fewer than three included articles limits evidence strength.")
        if forecast_input.current_price is None:
            limitations.append("Current quote price was unavailable.")
        if momentum is None:
            limitations.append("Previous close was unavailable, so momentum was not used.")
        return limitations

    def _top_factors(
        self,
        sentiment_score: Decimal,
        evidence_strength: Decimal,
        agreement: Decimal,
        momentum: Decimal | None,
    ) -> list[str]:
        factors = [
            f"Aggregate sentiment score: {sentiment_score:.5f}",
            f"Evidence strength score: {evidence_strength:.5f}",
            f"Sentiment agreement score: {agreement:.5f}",
        ]
        if momentum is not None:
            factors.append(f"Quote momentum versus previous close: {momentum:.5f}%")
        return factors

    def _target_end_time(self, quote_time: datetime | None, horizon: str) -> datetime | None:
        start = quote_time or datetime.now(timezone.utc)
        if horizon == "next_close":
            return self._add_trading_days(start, 1)
        if horizon == "3_trading_days":
            return self._add_trading_days(start, 3)
        if horizon == "7_trading_days":
            return self._add_trading_days(start, 7)
        return None

    def _add_trading_days(self, start: datetime, trading_days: int) -> datetime:
        current = start
        remaining = trading_days
        while remaining:
            current += timedelta(days=1)
            if current.weekday() < 5:
                remaining -= 1
        return current

    def _decimal_to_str(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return str(value)

    def _datetime_to_str(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()
