from app.market_data.provider import MarketDataProvider
from app.market_data.yfinance_provider import YFinanceMarketDataProvider


def get_market_data_provider() -> MarketDataProvider:
    return YFinanceMarketDataProvider()
