from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import yfinance as yf

from app.market_data.provider import MarketClose, MarketQuote


class MarketDataProviderError(RuntimeError):
    pass


class YFinanceMarketDataProvider:
    provider_name = "yfinance"

    def get_quote(self, ticker: str) -> MarketQuote:
        symbol = ticker.upper().strip()
        yf_ticker = yf.Ticker(symbol)

        fast_info = self._as_dict(getattr(yf_ticker, "fast_info", {}) or {})
        info = self._safe_info(yf_ticker)
        history = yf_ticker.history(period="5d", interval="1d", auto_adjust=False)

        if history.empty and not fast_info and not info:
            raise MarketDataProviderError(f"No market data returned for ticker {symbol}.")

        latest = history.iloc[-1].to_dict() if not history.empty else {}
        latest_index = history.index[-1] if not history.empty else None
        quote_time = self._to_datetime(latest_index)

        price = self._decimal(
            self._first_present(
                fast_info,
                ["last_price", "lastPrice"],
                latest.get("Close"),
                info.get("currentPrice"),
                info.get("regularMarketPrice"),
            )
        )
        previous_close = self._decimal(
            self._first_present(
                fast_info,
                ["previous_close", "previousClose"],
                info.get("previousClose"),
                info.get("regularMarketPreviousClose"),
            )
        )

        if price is None and previous_close is None:
            raise MarketDataProviderError(f"Market quote for {symbol} did not include a price.")

        return MarketQuote(
            ticker=symbol,
            price=price,
            previous_close=previous_close,
            open=self._decimal(self._first_present(fast_info, ["open"], latest.get("Open"))),
            day_high=self._decimal(
                self._first_present(
                    fast_info,
                    ["day_high", "dayHigh"],
                    latest.get("High"),
                    info.get("dayHigh"),
                    info.get("regularMarketDayHigh"),
                )
            ),
            day_low=self._decimal(
                self._first_present(
                    fast_info,
                    ["day_low", "dayLow"],
                    latest.get("Low"),
                    info.get("dayLow"),
                    info.get("regularMarketDayLow"),
                )
            ),
            volume=self._integer(
                self._first_present(
                    fast_info,
                    ["last_volume", "lastVolume"],
                    latest.get("Volume"),
                    info.get("volume"),
                    info.get("regularMarketVolume"),
                )
            ),
            quote_time=quote_time,
            provider=self.provider_name,
            market_cap=self._integer(
                self._first_present(fast_info, ["market_cap", "marketCap"], info.get("marketCap"))
            ),
            fifty_two_week_high=self._decimal(
                self._first_present(
                    fast_info,
                    ["year_high", "yearHigh"],
                    info.get("fiftyTwoWeekHigh"),
                )
            ),
            fifty_two_week_low=self._decimal(
                self._first_present(
                    fast_info,
                    ["year_low", "yearLow"],
                    info.get("fiftyTwoWeekLow"),
                )
            ),
            moving_average_50=self._decimal(info.get("fiftyDayAverage")),
            moving_average_200=self._decimal(info.get("twoHundredDayAverage")),
            beta=self._decimal(info.get("beta")),
            pe_ratio=self._decimal(info.get("trailingPE")),
            raw_payload={"fast_info": fast_info, "info": self._compact_info(info)},
        )

    def get_close_on_or_after(self, ticker: str, target_date: date) -> MarketClose:
        symbol = ticker.upper().strip()
        yf_ticker = yf.Ticker(symbol)
        end_date = target_date + timedelta(days=10)
        history = yf_ticker.history(
            start=target_date.isoformat(),
            end=end_date.isoformat(),
            interval="1d",
            auto_adjust=False,
        )

        if history.empty:
            raise MarketDataProviderError(
                f"No historical close returned for {symbol} on or after {target_date}."
            )

        for index, row in history.iterrows():
            close_price = self._decimal(row.get("Close"))
            close_date = self._to_datetime(index)
            if close_price is not None and close_date is not None:
                return MarketClose(
                    ticker=symbol,
                    close_price=close_price,
                    close_date=close_date.date(),
                    provider=self.provider_name,
                )

        raise MarketDataProviderError(
            f"Historical data for {symbol} did not include a usable close price."
        )

    def _safe_info(self, yf_ticker: yf.Ticker) -> dict[str, Any]:
        try:
            return dict(yf_ticker.info or {})
        except Exception:
            return {}

    def _as_dict(self, value: Any) -> dict[str, Any]:
        try:
            return dict(value)
        except Exception:
            return {}

    def _first_present(
        self, mapping: dict[str, Any], keys: list[str], *fallbacks: Any
    ) -> Any | None:
        for key in keys:
            value = mapping.get(key)
            if value is not None:
                return value
        for value in fallbacks:
            if value is not None:
                return value
        return None

    def _decimal(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _integer(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if hasattr(value, "to_pydatetime"):
            value = value.to_pydatetime()
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        return None

    def _compact_info(self, info: dict[str, Any]) -> dict[str, Any]:
        keys = [
            "symbol",
            "shortName",
            "quoteType",
            "exchange",
            "currency",
            "sector",
            "industry",
            "marketCap",
            "currentPrice",
            "regularMarketPrice",
            "previousClose",
            "dayHigh",
            "dayLow",
            "volume",
            "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow",
            "fiftyDayAverage",
            "twoHundredDayAverage",
            "beta",
            "trailingPE",
        ]
        return {key: info[key] for key in keys if key in info}
