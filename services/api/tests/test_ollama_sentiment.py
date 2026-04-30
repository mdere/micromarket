import json

import httpx
import pytest

from app.core.config import Settings
from app.sentiment.baseline import BaselineSentimentProvider
from app.sentiment.dependencies import get_sentiment_provider
from app.sentiment.ollama_provider import OllamaSentimentProvider
from app.sentiment.provider import SentimentProviderError


def _response(payload: dict, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", "http://localhost:11434/api/chat")
    return httpx.Response(status_code, json=payload, request=request)


def test_ollama_sentiment_scores_valid_json_response() -> None:
    def fake_post(*args, **kwargs) -> httpx.Response:
        return _response(
            {
                "message": {
                    "content": json.dumps(
                        {
                            "label": "positive",
                            "score": 0.42,
                            "confidence": 0.68,
                            "drivers": ["earnings", "demand"],
                            "evidence_snippets": ["AMD raised guidance."],
                            "limitations": ["Single article."],
                        }
                    )
                }
            }
        )

    provider = OllamaSentimentProvider(model="llama3.1:8b", post=fake_post)

    result = provider.score_article("AMD raised guidance as demand improved.", ticker="AMD")

    assert result.provider == "ollama"
    assert result.model_name == "ollama-chat-sentiment"
    assert result.model_version == "0.1.0:llama3.1:8b"
    assert result.label == "positive"
    assert result.score == 0.42
    assert result.confidence == 0.68
    assert result.drivers == ["earnings", "demand"]
    assert result.evidence_snippets == ["AMD raised guidance."]


def test_ollama_sentiment_prompt_requests_grounded_driver_coverage() -> None:
    captured_payload = {}

    def fake_post(*args, **kwargs) -> httpx.Response:
        captured_payload.update(kwargs["json"])
        return _response(
            {
                "message": {
                    "content": json.dumps(
                        {
                            "label": "mixed",
                            "score": 0.05,
                            "confidence": 0.62,
                            "drivers": ["demand", "supply", "uncertainty"],
                            "evidence_snippets": ["demand improved but supply constraints remain"],
                            "limitations": ["Single article."],
                        }
                    )
                }
            }
        )

    provider = OllamaSentimentProvider(post=fake_post)

    provider.score_article("AMD demand improved but supply constraints remain.", ticker="AMD")

    messages = captured_payload["messages"]
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    assert "Do not provide investment advice" in system_prompt
    assert "Driver rules" in user_prompt
    assert "for a mixed label" in user_prompt
    assert "do not include a driver unless it is supported by an evidence snippet" in user_prompt
    assert "use guidance for raised, lowered, cut, or warned guidance" in user_prompt


def test_ollama_sentiment_rejects_invalid_json_without_fallback() -> None:
    def fake_post(*args, **kwargs) -> httpx.Response:
        return _response({"message": {"content": "not json"}})

    provider = OllamaSentimentProvider(post=fake_post)

    with pytest.raises(SentimentProviderError, match="not valid JSON"):
        provider.score_article("AMD demand improved.", ticker="AMD")


def test_ollama_sentiment_rejects_missing_required_fields() -> None:
    def fake_post(*args, **kwargs) -> httpx.Response:
        return _response({"message": {"content": json.dumps({"label": "positive"})}})

    provider = OllamaSentimentProvider(post=fake_post)

    with pytest.raises(SentimentProviderError, match="missing required fields"):
        provider.score_article("AMD demand improved.", ticker="AMD")


def test_ollama_sentiment_accepts_single_string_list_fields() -> None:
    def fake_post(*args, **kwargs) -> httpx.Response:
        return _response(
            {
                "message": {
                    "content": json.dumps(
                        {
                            "label": "mixed",
                            "score": 0.05,
                            "confidence": 0.62,
                            "drivers": "demand, guidance, uncertainty",
                            "evidence_snippets": "CRM beat earnings but cut guidance.",
                            "limitations": "Single article.",
                        }
                    )
                }
            }
        )

    provider = OllamaSentimentProvider(post=fake_post)

    result = provider.score_article("CRM beat earnings but cut guidance.", ticker="CRM")

    assert result.label == "mixed"
    assert result.drivers == ["demand", "guidance", "uncertainty"]
    assert result.evidence_snippets == ["CRM beat earnings but cut guidance."]
    assert result.limitations == ["Single article."]


def test_ollama_sentiment_falls_back_to_baseline_on_timeout() -> None:
    def fake_post(*args, **kwargs) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    provider = OllamaSentimentProvider(
        fallback_provider=BaselineSentimentProvider(),
        post=fake_post,
    )

    result = provider.score_article("AMD demand improved and guidance was strong.", ticker="AMD")

    assert result.provider == "baseline"
    assert result.label == "positive"
    assert any("Ollama sentiment provider failed" in item for item in result.limitations)


def test_sentiment_dependency_selects_baseline_by_default() -> None:
    provider = get_sentiment_provider(Settings(_env_file=None))

    assert isinstance(provider, BaselineSentimentProvider)


def test_sentiment_dependency_selects_ollama_with_baseline_fallback() -> None:
    provider = get_sentiment_provider(
        Settings(
            SENTIMENT_PROVIDER="ollama",
            SENTIMENT_PROVIDER_FALLBACK="baseline",
            _env_file=None,
        )
    )

    assert isinstance(provider, OllamaSentimentProvider)
    assert isinstance(provider.fallback_provider, BaselineSentimentProvider)


def test_sentiment_dependency_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported SENTIMENT_PROVIDER"):
        get_sentiment_provider(Settings(SENTIMENT_PROVIDER="unknown", _env_file=None))
