from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Asset, ForecastOutcome, ForecastRun
from app.db.session import get_db
from app.evaluation.metrics import (
    absolute_error,
    direction_correct,
    direction_from_percent_change,
    percent_change,
)
from app.market_data.dependencies import get_market_data_provider
from app.market_data.provider import MarketDataProvider
from app.market_data.yfinance_provider import MarketDataProviderError

router = APIRouter()


@router.post("/refresh")
def refresh_evaluations(
    db: Session = Depends(get_db),
    market_data_provider: MarketDataProvider = Depends(get_market_data_provider),
) -> dict[str, object]:
    as_of = datetime.now(timezone.utc)
    forecasts = db.scalars(
        select(ForecastRun)
        .where(ForecastRun.target_end_time.is_not(None))
        .where(ForecastRun.target_end_time <= as_of)
        .where(
            ~select(ForecastOutcome.id)
            .where(ForecastOutcome.forecast_run_id == ForecastRun.id)
            .exists()
        )
        .order_by(ForecastRun.target_end_time.asc())
        .limit(100)
    ).all()

    evaluated = 0
    skipped = 0
    errors: list[dict[str, str]] = []

    for forecast in forecasts:
        asset = db.get(Asset, forecast.asset_id)
        if asset is None or forecast.target_end_time is None:
            skipped += 1
            continue

        try:
            close = market_data_provider.get_close_on_or_after(
                asset.symbol, forecast.target_end_time.date()
            )
        except MarketDataProviderError as exc:
            skipped += 1
            errors.append({"forecast_run_id": forecast.id, "message": str(exc)})
            continue

        actual_percent_change = percent_change(forecast.target_start_price, close.close_price)
        actual_direction = direction_from_percent_change(actual_percent_change)
        db.add(
            ForecastOutcome(
                forecast_run_id=forecast.id,
                actual_end_price=close.close_price,
                actual_percent_change=actual_percent_change,
                actual_direction=actual_direction,
                direction_correct=direction_correct(
                    forecast.predicted_direction, actual_direction
                ),
                absolute_error=absolute_error(
                    forecast.predicted_percent_change, actual_percent_change
                ),
                baseline_direction_correct=direction_correct(
                    forecast.baseline_direction, actual_direction
                ),
                baseline_absolute_error=absolute_error(
                    forecast.baseline_percent_change or Decimal("0"), actual_percent_change
                ),
            )
        )
        evaluated += 1

    db.commit()
    return {
        "status": "completed",
        "evaluated_forecasts": evaluated,
        "skipped_forecasts": skipped,
        "errors": errors,
    }


@router.get("/summary")
def evaluation_summary(db: Session = Depends(get_db)) -> dict[str, object]:
    rows = db.execute(
        select(
            ForecastRun.horizon,
            func.count(ForecastOutcome.id),
            func.avg(ForecastOutcome.absolute_error),
            func.avg(ForecastOutcome.baseline_absolute_error),
        )
        .join(ForecastOutcome, ForecastOutcome.forecast_run_id == ForecastRun.id)
        .group_by(ForecastRun.horizon)
        .order_by(ForecastRun.horizon)
    ).all()

    evaluated_forecasts = db.scalar(select(func.count(ForecastOutcome.id))) or 0
    direction_rows = db.execute(
        select(ForecastRun.horizon, ForecastOutcome.direction_correct)
        .join(ForecastOutcome, ForecastOutcome.forecast_run_id == ForecastRun.id)
        .where(ForecastOutcome.direction_correct.is_not(None))
    ).all()

    direction_counts: dict[str, dict[str, int]] = {}
    for horizon, is_correct in direction_rows:
        bucket = direction_counts.setdefault(horizon, {"correct": 0, "total": 0})
        bucket["total"] += 1
        if is_correct:
            bucket["correct"] += 1

    return {
        "evaluated_forecasts": evaluated_forecasts,
        "by_horizon": [
            {
                "horizon": horizon,
                "evaluated_forecasts": count,
                "directional_accuracy": _accuracy(direction_counts.get(horizon)),
                "mean_absolute_error": _decimal_to_str(mean_absolute_error),
                "baseline_mean_absolute_error": _decimal_to_str(
                    baseline_mean_absolute_error
                ),
            }
            for horizon, count, mean_absolute_error, baseline_mean_absolute_error in rows
        ],
    }


def _accuracy(counts: dict[str, int] | None) -> str | None:
    if not counts or counts["total"] == 0:
        return None
    return str(Decimal(counts["correct"]) / Decimal(counts["total"]))


def _decimal_to_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)
