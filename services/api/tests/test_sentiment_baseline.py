import json
from pathlib import Path

import pytest

from app.sentiment.baseline import BaselineSentimentProvider


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sentiment_curated_examples.json"


def test_baseline_sentiment_scores_positive_text() -> None:
    provider = BaselineSentimentProvider()

    result = provider.score_article(
        "Demand improved and earnings growth looked resilient for SPY.",
        ticker="SPY",
    )

    assert result.label == "positive"
    assert result.score > 0
    assert result.confidence > 0.25
    assert result.drivers
    assert result.evidence_snippets


def test_baseline_sentiment_scores_negative_text() -> None:
    provider = BaselineSentimentProvider()

    result = provider.score_article(
        "AAPL warned that demand was weaker and margin pressure created downside risk.",
        ticker="AAPL",
    )

    assert result.label == "negative"
    assert result.score < 0
    assert result.confidence > 0.25
    assert result.drivers


def test_baseline_sentiment_scores_neutral_text() -> None:
    provider = BaselineSentimentProvider()

    result = provider.score_article(
        "The company released a routine operational update with no clear forecast details.",
        ticker="MSFT",
    )

    assert result.label == "neutral"
    assert result.score == 0
    assert "No baseline sentiment keywords were found." in result.limitations


def test_baseline_sentiment_detects_mixed_finance_text() -> None:
    provider = BaselineSentimentProvider()

    result = provider.score_article(
        (
            "NVDA advanced on strong data-center demand and revenue growth, but valuation "
            "concerns, supply constraints, and uncertainty limited conviction."
        ),
        ticker="NVDA",
    )

    assert result.label == "mixed"
    assert -0.4 <= result.score <= 0.4
    assert any(driver.startswith("demand:") for driver in result.drivers)
    assert any(driver.startswith("valuation:") for driver in result.drivers)
    assert "Positive and negative baseline signals were both present." in result.limitations


def test_baseline_sentiment_handles_negated_positive_signal() -> None:
    provider = BaselineSentimentProvider()

    result = provider.score_article(
        "META ad checks were not strong and showed no revenue growth. Demand trends were unclear.",
        ticker="META",
    )

    assert result.label == "negative"
    assert result.score < 0
    assert any(driver.startswith("demand:") for driver in result.drivers)
    assert "Uncertainty language reduced baseline sentiment confidence." in result.limitations


@pytest.mark.parametrize("example", json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
def test_baseline_sentiment_curated_fixtures(example: dict) -> None:
    provider = BaselineSentimentProvider()

    result = provider.score_article(example["text"], ticker=example["ticker"])

    assert result.model_version == "0.2.0"
    assert result.label == example["expected_label"]
    assert example["expected_score_min"] <= result.score <= example["expected_score_max"]
    for expected_driver in example["expected_drivers"]:
        assert any(driver.startswith(f"{expected_driver}:") for driver in result.drivers)
