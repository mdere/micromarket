from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class MarketQuote:
    ticker: str
    price: Decimal | None
    previous_close: Decimal | None
    open: Decimal | None = None
    day_high: Decimal | None = None
    day_low: Decimal | None = None
    volume: int | None = None
    quote_time: datetime | None = None
    provider: str = "unknown"
    market_cap: int | None = None
    fifty_two_week_high: Decimal | None = None
    fifty_two_week_low: Decimal | None = None
    moving_average_50: Decimal | None = None
    moving_average_200: Decimal | None = None
    beta: Decimal | None = None
    pe_ratio: Decimal | None = None
    raw_payload: dict | None = None


@dataclass(frozen=True)
class MarketClose:
    ticker: str
    close_price: Decimal
    close_date: date
    provider: str = "unknown"


@dataclass(frozen=True)
class MarketPrice:
    ticker: str
    price_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    adjusted_close: Decimal | None = None
    volume: int | None = None
    provider: str = "unknown"
    raw_payload: dict | None = None


class MarketDataProvider(Protocol):
    def get_quote(self, ticker: str) -> MarketQuote:
        """Return a market quote for a ticker."""

    def get_close_on_or_after(self, ticker: str, target_date: date) -> MarketClose:
        """Return the first available daily close on or after target_date."""

    def get_price_history(self, ticker: str, start: date, end: date) -> list[MarketPrice]:
        """Return daily market prices between start and end, inclusive where available."""
