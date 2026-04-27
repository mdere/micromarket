from datetime import datetime, timezone
from decimal import Decimal

from app.forecasting.baseline import BaselineForecastProvider
from app.forecasting.provider import ForecastInput


def test_baseline_forecast_generates_mvp_horizons() -> None:
    provider = BaselineForecastProvider()

    forecasts = provider.generate_forecasts(
        ForecastInput(
            ticker="SPY",
            quote_provider="fake-market-data",
            current_price=Decimal("512.34"),
            previous_close=Decimal("510.12"),
            quote_time=datetime(2026, 4, 24, 16, 0, tzinfo=timezone.utc),
            sentiment_score=Decimal("1.0"),
            agreement_score=Decimal("1.0"),
            evidence_strength_score=Decimal("1.0"),
            article_count=3,
            included_article_count=3,
        )
    )

    assert [forecast.horizon for forecast in forecasts] == [
        "next_close",
        "3_trading_days",
        "7_trading_days",
    ]
    assert forecasts[1].predicted_direction == "up"
    assert forecasts[1].baseline_direction == "flat"
    assert forecasts[1].feature_snapshot["quote_provider"] == "fake-market-data"
    assert forecasts[1].target_start_price == Decimal("512.34")
    assert forecasts[1].target_end_time is not None


def test_baseline_forecast_marks_weak_signal_uncertain() -> None:
    provider = BaselineForecastProvider()

    forecast = provider.generate_forecasts(
        ForecastInput(
            ticker="AAPL",
            quote_provider="fake-market-data",
            current_price=Decimal("100"),
            previous_close=Decimal("100"),
            quote_time=None,
            sentiment_score=Decimal("0"),
            agreement_score=Decimal("1.0"),
            evidence_strength_score=Decimal("0.33333"),
            article_count=1,
            included_article_count=1,
        )
    )[1]

    assert forecast.predicted_direction == "uncertain"
    assert forecast.predicted_percent_change == 0.0
    assert "Fewer than three included articles" in forecast.limitations[2]
