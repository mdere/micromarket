from app.forecasting.baseline import BaselineForecastProvider
from app.forecasting.provider import ForecastProvider


def get_forecast_provider() -> ForecastProvider:
    return BaselineForecastProvider()
