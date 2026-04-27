from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Analysis, Asset, Base, ForecastRun
from app.db.session import get_db
from app.main import app
from app.market_data.dependencies import get_market_data_provider
from app.market_data.provider import MarketClose, MarketQuote


class FakeEvaluationMarketDataProvider:
    def get_quote(self, ticker: str) -> MarketQuote:
        return MarketQuote(ticker=ticker.upper(), price=Decimal("105"), previous_close=Decimal("100"))

    def get_close_on_or_after(self, ticker: str, target_date: date) -> MarketClose:
        return MarketClose(
            ticker=ticker.upper(),
            close_price=Decimal("105.000000"),
            close_date=target_date,
            provider="fake-market-data",
        )


def build_test_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_market_data_provider] = lambda: FakeEvaluationMarketDataProvider()
    return TestClient(app), testing_session


def test_refresh_evaluations_persists_expired_forecast_outcome() -> None:
    client, testing_session = build_test_app()

    try:
        forecast_id = _seed_expired_forecast(testing_session)

        response = client.post("/evaluations/refresh")

        assert response.status_code == 200
        assert response.json()["evaluated_forecasts"] == 1
        assert response.json()["skipped_forecasts"] == 0

        summary = client.get("/evaluations/summary")

        assert summary.status_code == 200
        assert summary.json()["evaluated_forecasts"] == 1
        by_horizon = summary.json()["by_horizon"][0]
        assert by_horizon["horizon"] == "3_trading_days"
        assert by_horizon["directional_accuracy"] == "1"
        assert by_horizon["mean_absolute_error"] == "1.0"
        assert by_horizon["baseline_mean_absolute_error"] == "5.0"

        second_refresh = client.post("/evaluations/refresh")

        assert second_refresh.status_code == 200
        assert second_refresh.json()["evaluated_forecasts"] == 0
        assert forecast_id is not None
    finally:
        app.dependency_overrides.clear()


def _seed_expired_forecast(testing_session: sessionmaker[Session]) -> str:
    db = testing_session()
    try:
        asset = Asset(symbol="SPY", asset_type="etf", currency="USD")
        db.add(asset)
        db.flush()
        analysis = Analysis(
            asset_id=asset.id,
            status="completed",
            primary_horizon="3_trading_days",
            input_mode="manual_text",
            limitations=[],
        )
        db.add(analysis)
        db.flush()
        forecast = ForecastRun(
            analysis_id=analysis.id,
            asset_id=asset.id,
            horizon="3_trading_days",
            provider="baseline",
            model_name="forecast-rule-baseline",
            model_version="0.1.0",
            predicted_direction="up",
            predicted_percent_change=Decimal("4.00000"),
            confidence_score=Decimal("0.65000"),
            baseline_direction="flat",
            baseline_percent_change=Decimal("0.00000"),
            feature_snapshot={},
            top_factors=[],
            limitations=[],
            target_start_price=Decimal("100.000000"),
            target_start_time=datetime(2026, 4, 20, 16, 0, tzinfo=timezone.utc),
            target_end_time=datetime(2026, 4, 23, 16, 0, tzinfo=timezone.utc),
        )
        db.add(forecast)
        db.commit()
        return forecast.id
    finally:
        db.close()
