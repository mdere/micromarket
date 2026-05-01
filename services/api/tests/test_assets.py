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
from app.main import app
from app.market_data.dependencies import get_market_data_provider
from app.market_data.provider import MarketPrice, MarketQuote


class FakeMarketDataProvider:
    def get_quote(self, ticker: str) -> MarketQuote:
        return MarketQuote(
            ticker=ticker.upper(),
            price=Decimal("100.000000"),
            previous_close=Decimal("99.000000"),
            quote_time=datetime(2026, 5, 1, 16, 0, tzinfo=timezone.utc),
            provider="fake-market-data",
        )

    def get_price_history(self, ticker: str, start: date, end: date) -> list[MarketPrice]:
        prices: list[MarketPrice] = []
        current = start
        index = 0
        while current <= end:
            if current.weekday() < 5:
                close = Decimal("100.000000") + Decimal(index)
                prices.append(
                    MarketPrice(
                        ticker=ticker.upper(),
                        price_date=current,
                        open=close,
                        high=close + Decimal("1.000000"),
                        low=close - Decimal("1.000000"),
                        close=close,
                        adjusted_close=close,
                        volume=1000000 + index,
                        provider="fake-market-data",
                    )
                )
                index += 1
            current += timedelta(days=1)
        return prices


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
        return Settings(ARTIFACT_ROOT=str(tmp_path), SENTIMENT_PROVIDER="baseline")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_market_data_provider] = lambda: FakeMarketDataProvider()
    return TestClient(app)


def test_onboard_asset_workspace_and_search(tmp_path) -> None:
    client = build_test_app(tmp_path)

    try:
        onboarded = client.post("/assets/onboard", json={"symbol": "tsm", "name": "TSMC"})

        assert onboarded.status_code == 201
        workspace = onboarded.json()
        assert workspace["symbol"] == "TSM"
        assert workspace["name"] == "TSMC"
        assert workspace["analysis_count"] == 0
        assert workspace["market_history_count"] > 0
        assert workspace["onboarding_status"] == "onboarded"

        search = client.get("/assets?query=ts")

        assert search.status_code == 200
        assert [item["symbol"] for item in search.json()] == ["TSM"]
    finally:
        app.dependency_overrides.clear()
