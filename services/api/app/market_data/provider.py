from dataclasses import dataclass
from datetime import datetime
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


class MarketDataProvider(Protocol):
    def get_quote(self, ticker: str) -> MarketQuote:
        """Return a market quote for a ticker."""
