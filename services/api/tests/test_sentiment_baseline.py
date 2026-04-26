from app.sentiment.baseline import BaselineSentimentProvider


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
