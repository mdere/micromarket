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
from app.ingestion.dependencies import get_url_extraction_provider
from app.ingestion.url_provider import URLExtractionError, URLExtractionResult
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


class FakeURLExtractionProvider:
    def extract(self, url: str) -> URLExtractionResult:
        return URLExtractionResult(
            url=url,
            final_url="https://example.com/final-spy-article",
            title="Extracted SPY article",
            source="Example News",
            text=(
                "SPY demand improved as market breadth expanded. "
                "The article noted resilient flows and constructive momentum."
            ),
            raw_html="<html><body><article>SPY demand improved.</article></body></html>",
        )


class FailingURLExtractionProvider:
    def extract(self, url: str) -> URLExtractionResult:
        raise URLExtractionError(f"No article text could be extracted from {url}.")


def build_test_app(tmp_path, url_extraction_provider=None):
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
    app.dependency_overrides[get_url_extraction_provider] = (
        lambda: url_extraction_provider or FakeURLExtractionProvider()
    )
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
        assert created["sentiment_aggregate"]["included_article_count"] == 1
        assert created["sentiment_aggregate"]["positive_count"] == 1
        assert created["sentiment_aggregate"]["aggregate_score"] == "1.00000"
        assert created["articles"][0]["included_in_forecast"] is True
        assert created["articles"][0]["relevance_score"] == "0.90000"
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
        assert "manual text or an absolute URL" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_with_url_article(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "spy",
                "articles": [
                    {
                        "url": "https://example.com/spy-article",
                    }
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        assert created["input_mode"] == "url"
        assert created["articles"][0]["title"] == "Extracted SPY article"
        assert created["articles"][0]["source"] == "Example News"
        assert created["articles"][0]["url"] == "https://example.com/final-spy-article"
        assert created["articles"][0]["input_type"] == "url"
        assert created["sentiment_runs"][0]["sentiment_label"] == "positive"
        assert len(created["forecast_runs"]) == 3
        assert created["articles"][0]["included_in_forecast"] is True
        assert created["articles"][0]["relevance_score"] == "1.00000"

        raw_artifact_path = created["articles"][0]["raw_artifact_path"]
        assert raw_artifact_path is not None
        assert raw_artifact_path.endswith(".html")
        assert "SPY demand improved" in open(raw_artifact_path, encoding="utf-8").read()
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_excludes_duplicate_article_from_aggregate(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        article_text = "SPY saw improving demand and resilient market breadth."
        response = client.post(
            "/analyses",
            json={
                "ticker": "spy",
                "articles": [
                    {"title": "First SPY note", "text": article_text},
                    {"title": "Second SPY note", "text": article_text},
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        assert created["sentiment_aggregate"]["article_count"] == 2
        assert created["sentiment_aggregate"]["included_article_count"] == 1
        assert len(created["sentiment_runs"]) == 2
        assert created["articles"][0]["included_in_forecast"] is True
        assert created["articles"][1]["included_in_forecast"] is False
        assert created["articles"][1]["duplicate_group_id"] == created["articles"][1]["content_hash"]
        assert "Duplicate article content" in created["articles"][1]["exclusion_reason"]
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_excludes_low_relevance_article_from_aggregate(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "AAPL",
                "articles": [
                    {
                        "title": "Recipe note",
                        "text": "This recipe explains how to bake bread with flour and water.",
                    }
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        assert created["sentiment_aggregate"]["article_count"] == 1
        assert created["sentiment_aggregate"]["included_article_count"] == 0
        assert created["sentiment_aggregate"]["evidence_strength_score"] == "0.00000"
        assert created["articles"][0]["included_in_forecast"] is False
        assert created["articles"][0]["relevance_score"] == "0.00000"
        assert "did not reference the requested ticker" in created["articles"][0]["exclusion_reason"]
        primary_forecast = next(
            run for run in created["forecast_runs"] if run["horizon"] == "3_trading_days"
        )
        assert primary_forecast["feature_snapshot"]["included_article_count"] == 0
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_excludes_market_article_for_wrong_ticker(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "AMD",
                "articles": [
                    {
                        "title": "Why NVIDIA stock moved today",
                        "source": "manual note",
                        "url": "https://example.com/markets/nvidia-nvda-stock",
                        "text": (
                            "NVIDIA shares moved after analysts discussed market demand, "
                            "earnings momentum, and AI chip revenue."
                        ),
                    }
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        assert created["ticker"] == "AMD"
        assert created["sentiment_aggregate"]["article_count"] == 1
        assert created["sentiment_aggregate"]["included_article_count"] == 0
        assert created["articles"][0]["included_in_forecast"] is False
        assert created["articles"][0]["relevance_score"] == "0.15000"
        assert "did not reference the requested ticker" in created["articles"][0]["exclusion_reason"]
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_reports_url_extraction_failure(tmp_path) -> None:
    client = build_test_app(tmp_path, url_extraction_provider=FailingURLExtractionProvider())

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "SPY",
                "articles": [{"url": "https://example.com/no-text"}],
            },
        )

        assert response.status_code == 502
        assert "No article text could be extracted" in response.json()["detail"]
        failed = client.get("/analyses?ticker=SPY")
        assert failed.status_code == 200
        assert failed.json()[0]["status"] == "failed"
        assert "No article text could be extracted" in failed.json()[0]["error_message"]
    finally:
        app.dependency_overrides.clear()


def test_list_analyses_can_filter_by_ticker(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        for ticker in ("AMD", "SPY", "AMD"):
            response = client.post(
                "/analyses",
                json={
                    "ticker": ticker,
                    "articles": [
                        {
                            "title": f"{ticker} note",
                            "source": "manual note",
                            "text": f"{ticker} saw improving demand and resilient market breadth.",
                        }
                    ],
                },
            )
            assert response.status_code == 201

        all_response = client.get("/analyses")
        amd_response = client.get("/analyses?ticker=amd")

        assert all_response.status_code == 200
        assert len(all_response.json()) == 3
        assert amd_response.status_code == 200
        assert [analysis["ticker"] for analysis in amd_response.json()] == ["AMD", "AMD"]
        assert all(analysis["created_at"] for analysis in amd_response.json())
    finally:
        app.dependency_overrides.clear()
