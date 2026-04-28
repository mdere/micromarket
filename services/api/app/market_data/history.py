from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset, MarketPriceHistory, TickerContext, utc_now
from app.market_data.provider import MarketDataProvider


@dataclass(frozen=True)
class MarketHistoryContext:
    provider: str
    lookback_days: int
    history_start_date: date | None
    history_end_date: date | None
    feature_window_start_time: datetime | None
    feature_window_end_time: datetime | None
    target_start_price: Decimal | None
    previous_close: Decimal | None
    stored_price_count: int


def ensure_market_history(
    db: Session,
    asset: Asset,
    ticker: str,
    provider: MarketDataProvider,
    analysis_as_of: datetime,
    lookback_days: int,
) -> MarketHistoryContext:
    end_date = analysis_as_of.date()
    start_date = end_date - timedelta(days=lookback_days)
    prices = provider.get_price_history(ticker, start=start_date, end=end_date)
    provider_name = prices[0].provider if prices else "unknown"

    existing_dates = set(
        db.scalars(
            select(MarketPriceHistory.price_date)
            .where(MarketPriceHistory.asset_id == asset.id)
            .where(MarketPriceHistory.provider == provider_name)
            .where(MarketPriceHistory.price_date >= start_date)
            .where(MarketPriceHistory.price_date <= end_date)
        ).all()
    )

    for price in prices:
        if price.price_date in existing_dates:
            continue
        db.add(
            MarketPriceHistory(
                asset_id=asset.id,
                provider=price.provider,
                price_date=price.price_date,
                open=price.open,
                high=price.high,
                low=price.low,
                close=price.close,
                adjusted_close=price.adjusted_close,
                volume=price.volume,
            )
        )

    context = db.scalar(
        select(TickerContext)
        .where(TickerContext.asset_id == asset.id)
        .where(TickerContext.provider == provider_name)
        .where(TickerContext.lookback_days == lookback_days)
    )
    if context is None:
        context = TickerContext(
            asset_id=asset.id,
            provider=provider_name,
            lookback_days=lookback_days,
        )
        db.add(context)

    context.history_start_date = start_date
    context.history_end_date = end_date
    context.last_backfilled_at = utc_now()

    usable_prices = sorted(
        [price for price in prices if price.close is not None and price.price_date <= end_date],
        key=lambda price: price.price_date,
    )
    latest = usable_prices[-1] if usable_prices else None
    previous = usable_prices[-2] if len(usable_prices) >= 2 else None

    return MarketHistoryContext(
        provider=provider_name,
        lookback_days=lookback_days,
        history_start_date=start_date,
        history_end_date=end_date,
        feature_window_start_time=_market_close_time(start_date),
        feature_window_end_time=_market_close_time(end_date),
        target_start_price=latest.close if latest is not None else None,
        previous_close=previous.close if previous is not None else None,
        stored_price_count=len(usable_prices),
    )


def _market_close_time(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time(hour=16), tzinfo=timezone.utc)
