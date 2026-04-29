from fastapi import Depends

from app.core.config import Settings, get_settings
from app.sentiment.baseline import BaselineSentimentProvider
from app.sentiment.ollama_provider import OllamaSentimentProvider
from app.sentiment.provider import SentimentProvider


def get_sentiment_provider(settings: Settings = Depends(get_settings)) -> SentimentProvider:
    provider_name = settings.sentiment_provider.strip().lower()
    fallback_name = (settings.sentiment_provider_fallback or "").strip().lower()
    fallback_provider = BaselineSentimentProvider() if fallback_name == "baseline" else None

    if provider_name == "baseline":
        return BaselineSentimentProvider()
    if provider_name == "ollama":
        return OllamaSentimentProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_sentiment_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            fallback_provider=fallback_provider,
        )
    raise ValueError(f"Unsupported SENTIMENT_PROVIDER: {settings.sentiment_provider}")
