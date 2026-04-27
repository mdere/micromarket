from collections.abc import Generator
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.models import Base
from app.db.session import get_db
from app.main import app
from app.market_data.dependencies import get_market_data_provider
from app.market_data.provider import MarketQuote


class FakeMarketDataProvider:
    def get_quote(self, ticker: str) -> MarketQuote:
        return MarketQuote(
            ticker=ticker.upper(),
            price=Decimal("512.340000"),
            previous_close=Decimal("510.120000"),
            open=Decimal("511.000000"),
            day_high=Decimal("514.000000"),
            day_low=Decimal("509.500000"),
            volume=1234567,
            quote_time=datetime(2026, 4, 26, 16, 0, tzinfo=timezone.utc),
            provider="fake-market-data",
            market_cap=123000000,
        )


def build_test_app(tmp_path):
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

    def override_settings() -> Settings:
        return Settings(ARTIFACT_ROOT=str(tmp_path))

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_market_data_provider] = lambda: FakeMarketDataProvider()
    return TestClient(app)


def test_create_and_get_analysis(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "spy",
                "articles": [
                    {
                        "title": "SPY earnings sentiment",
                        "source": "manual note",
                        "text": "SPY saw improving breadth and resilient demand across large caps.",
                    }
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        assert created["ticker"] == "SPY"
        assert created["status"] == "completed"
        assert created["primary_horizon"] == "3_trading_days"
        assert created["market_quote"]["provider"] == "fake-market-data"
        assert created["market_quote"]["price"] == "512.340000"
        assert created["sentiment_runs"][0]["provider"] == "baseline"
        assert created["sentiment_runs"][0]["sentiment_label"] == "positive"
        assert created["sentiment_aggregate"]["article_count"] == 1
        assert created["sentiment_aggregate"]["positive_count"] == 1
        assert created["sentiment_aggregate"]["aggregate_score"] == "1.00000"
        assert len(created["forecast_runs"]) == 3
        primary_forecast = next(
            run for run in created["forecast_runs"] if run["horizon"] == "3_trading_days"
        )
        assert primary_forecast["provider"] == "baseline"
        assert primary_forecast["model_name"] == "forecast-rule-baseline"
        assert primary_forecast["predicted_direction"] == "up"
        assert primary_forecast["baseline_direction"] == "flat"
        assert primary_forecast["feature_snapshot"]["included_article_count"] == 1
        assert "Research-only forecast" in primary_forecast["limitations"][0]
        assert created["articles"][0]["word_count"] == 10
        artifact_path = created["articles"][0]["raw_artifact_path"]
        assert artifact_path is not None
        assert "SPY saw improving breadth" in open(artifact_path, encoding="utf-8").read()

        fetched = client.get(f"/analyses/{created['id']}")

        assert fetched.status_code == 200
        assert fetched.json()["id"] == created["id"]
        assert fetched.json()["market_quote"]["volume"] == 1234567
        assert fetched.json()["sentiment_aggregate"]["summary"].startswith(
            "Baseline sentiment is positive"
        )
        assert len(fetched.json()["forecast_runs"]) == 3
        assert fetched.json()["articles"][0]["content_hash"] == created["articles"][0]["content_hash"]
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_requires_manual_text(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post("/analyses", json={"ticker": "AAPL", "articles": []})

        assert response.status_code == 400
        assert "manual article" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
