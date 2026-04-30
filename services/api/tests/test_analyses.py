from collections.abc import Generator
from datetime import date, datetime, timedelta, timezone
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
from app.market_data.provider import MarketPrice, MarketQuote
from app.sentiment.dependencies import get_sentiment_provider
from app.sentiment.provider import SentimentProviderError


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

    def get_price_history(self, ticker: str, start: date, end: date) -> list[MarketPrice]:
        prices: list[MarketPrice] = []
        current = start
        index = 0
        while current <= end:
            if current.weekday() < 5:
                close = Decimal("500.000000") + Decimal(index)
                prices.append(
                    MarketPrice(
                        ticker=ticker.upper(),
                        price_date=current,
                        open=close - Decimal("1.000000"),
                        high=close + Decimal("2.000000"),
                        low=close - Decimal("2.000000"),
                        close=close,
                        adjusted_close=close,
                        volume=1000000 + index,
                        provider="fake-market-data",
                    )
                )
                index += 1
            current += timedelta(days=1)
        return prices


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


class FailingSentimentProvider:
    def score_article(self, article_text: str, ticker: str):
        raise SentimentProviderError("Sentiment provider unavailable.")


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
        return Settings(ARTIFACT_ROOT=str(tmp_path), SENTIMENT_PROVIDER="baseline")

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
        assert created["analysis_as_of_source"] == "live"
        assert created["ticker_context"]["lookback_days"] == 30
        assert created["ticker_context"]["stored_price_count"] > 0
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
        assert primary_forecast["feature_window_start_time"] is not None
        assert primary_forecast["feature_window_end_time"] is not None
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


def test_create_analysis_with_historical_article_uses_published_at_as_of(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "AMD",
                "articles": [
                    {
                        "title": "AMD historical article",
                        "published_at": "2026-03-05T14:30:00Z",
                        "text": "AMD saw improving demand and resilient AI chip momentum.",
                    }
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        assert created["analysis_as_of"] == "2026-03-05T14:30:00+00:00"
        assert created["analysis_as_of_source"] == "article_published_at"
        assert created["articles"][0]["published_at"] == "2026-03-05T14:30:00+00:00"
        assert created["ticker_context"]["history_end_date"].startswith("2026-03-05")

        primary_forecast = next(
            run for run in created["forecast_runs"] if run["horizon"] == "3_trading_days"
        )
        assert primary_forecast["target_start_time"] == "2026-03-05T14:30:00+00:00"
        assert primary_forecast["target_start_price"] != created["market_quote"]["price"]
        assert primary_forecast["feature_snapshot"]["analysis_as_of"] == (
            "2026-03-05T14:30:00+00:00"
        )
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_extracts_related_entities(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "NVDA",
                "articles": [
                    {
                        "title": "NVDA supply chain note",
                        "source": "manual note",
                        "text": (
                            "NVDA demand stayed strong as TSMC expanded foundry capacity. "
                            "Samsung also discussed HBM supply for AI chips."
                        ),
                    }
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        entities = created["articles"][0]["entities"]
        names = {entity["name"] for entity in entities}
        relationships = {entity["name"]: entity["relationship_type"] for entity in entities}

        assert "TSMC" in names
        assert "Samsung" in names
        assert "HBM" in names
        assert relationships["TSMC"] == "supplier"
        assert relationships["Samsung"] == "supplier"
        assert relationships["HBM"] == "product_exposure"
        tsmc = next(entity for entity in entities if entity["name"] == "TSMC")
        assert tsmc["symbol"] == "TSM"
        assert tsmc["provider"] == "deterministic"
        assert tsmc["model_name"] == "entity-alias-baseline"
        assert any("TSMC expanded foundry capacity" in snippet for snippet in tsmc["evidence_snippets"])
        tracking_needs = created["tracking_needs"]
        tracking_by_name = {need["name"]: need for need in tracking_needs}
        assert tracking_by_name["TSMC"]["suggested_symbol"] == "TSM"
        assert tracking_by_name["TSMC"]["related_asset_id"] is None
        assert tracking_by_name["TSMC"]["onboarding_status"] == "pending"
        assert tracking_by_name["TSMC"]["tracking_type"] == "supplier"
        assert tracking_by_name["TSMC"]["status"] == "suggested"
        assert "supplier connected" in tracking_by_name["TSMC"]["reason"]
        assert any(
            "TSMC expanded foundry capacity" in snippet
            for snippet in tracking_by_name["TSMC"]["evidence_snippets"]
        )
        assert tracking_by_name["Samsung"]["tracking_type"] == "supplier"
        assert tracking_by_name["HBM"]["tracking_type"] == "product_theme"
        assert tracking_by_name["HBM"]["suggested_symbol"] is None
        assert tracking_by_name["HBM"]["onboarding_status"] == "not_applicable"
        assert tracking_by_name["TSMC"]["provider"] == "deterministic"
        assert tracking_by_name["TSMC"]["model_name"] == "tracking-needs-baseline"
    finally:
        app.dependency_overrides.clear()


def test_update_tracking_need_status(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "NVDA",
                "articles": [
                    {
                        "title": "NVDA supplier note",
                        "source": "manual note",
                        "text": "NVDA demand stayed strong as TSMC expanded foundry capacity.",
                    }
                ],
            },
        )
        assert response.status_code == 201
        tracking_need = next(
            need for need in response.json()["tracking_needs"] if need["name"] == "TSMC"
        )

        updated = client.patch(
            f"/analyses/tracking-needs/{tracking_need['id']}",
            json={"status": "accepted"},
        )

        assert updated.status_code == 200
        assert updated.json()["id"] == tracking_need["id"]
        assert updated.json()["status"] == "accepted"
        assert updated.json()["related_asset_id"] is not None
        assert updated.json()["onboarding_status"] == "onboarded"
        fetched = client.get(f"/analyses/{response.json()['id']}")
        fetched_needs = {need["id"]: need for need in fetched.json()["tracking_needs"]}
        assert fetched_needs[tracking_need["id"]]["status"] == "accepted"
        assert fetched_needs[tracking_need["id"]]["related_asset_id"] == updated.json()[
            "related_asset_id"
        ]
    finally:
        app.dependency_overrides.clear()


def test_update_tracking_need_status_rejects_invalid_status(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "NVDA",
                "articles": [
                    {
                        "title": "NVDA supplier note",
                        "source": "manual note",
                        "text": "NVDA demand stayed strong as TSMC expanded foundry capacity.",
                    }
                ],
            },
        )
        assert response.status_code == 201
        tracking_need = response.json()["tracking_needs"][0]

        updated = client.patch(
            f"/analyses/tracking-needs/{tracking_need['id']}",
            json={"status": "promoted"},
        )

        assert updated.status_code == 400
        assert "accepted" in updated.json()["detail"]
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


def test_create_analysis_reports_sentiment_provider_failure(tmp_path) -> None:
    client = build_test_app(tmp_path)
    app.dependency_overrides[get_sentiment_provider] = lambda: FailingSentimentProvider()

    try:
        response = client.post(
            "/analyses",
            json={
                "ticker": "SPY",
                "articles": [
                    {
                        "title": "SPY sentiment provider failure",
                        "source": "manual note",
                        "text": "SPY demand improved as market breadth expanded.",
                    }
                ],
            },
        )

        assert response.status_code == 502
        assert response.json()["detail"] == "Sentiment provider unavailable."
        failed = client.get("/analyses?ticker=SPY")
        assert failed.status_code == 200
        assert failed.json()[0]["status"] == "failed"
        assert failed.json()[0]["error_message"] == "Sentiment provider unavailable."
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
