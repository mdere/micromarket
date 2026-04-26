from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class MarketQuote:
    ticker: str
    price: Decimal | None
    previous_close: Decimal | None
    volume: int | None
    quote_time: datetime | None
    provider: str


class MarketDataProvider(Protocol):
    def get_quote(self, ticker: str) -> MarketQuote:
        """Return a market quote for a ticker."""
