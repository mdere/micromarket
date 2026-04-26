from app.sentiment.baseline import BaselineSentimentProvider
from app.sentiment.provider import SentimentProvider


def get_sentiment_provider() -> SentimentProvider:
    return BaselineSentimentProvider()
