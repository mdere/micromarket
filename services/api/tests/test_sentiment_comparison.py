import pytest

from app.core.config import Settings
from app.sentiment.baseline import BaselineSentimentProvider
from app.sentiment.comparison import (
    build_ollama_provider,
    compare_fixtures,
    select_fixtures,
    write_reports,
)
from app.sentiment.provider import SentimentResult


class FakeProvider:
    def __init__(self, result: SentimentResult) -> None:
        self.result = result

    def score_article(self, article_text: str, ticker: str) -> SentimentResult:
        return self.result


def test_compare_fixtures_builds_review_rows() -> None:
    fixtures = [
        {
            "id": "example",
            "ticker": "AMD",
            "title": "AMD example",
            "text": "AMD raised guidance.",
            "expected_label": "positive",
            "expected_score_min": 0.2,
            "expected_score_max": 1.0,
            "expected_drivers": ["guidance"],
        }
    ]
    baseline = FakeProvider(
        SentimentResult(
            label="positive",
            score=0.5,
            confidence=0.7,
            drivers=["guidance"],
            evidence_snippets=["AMD raised guidance."],
            limitations=[],
            provider="baseline",
            model_name="baseline",
            model_version="test",
        )
    )
    ollama = FakeProvider(
        SentimentResult(
            label="mixed",
            score=0.1,
            confidence=0.6,
            drivers=["guidance", "valuation"],
            evidence_snippets=["AMD raised guidance."],
            limitations=["Single article."],
            provider="ollama",
            model_name="ollama",
            model_version="test",
        )
    )

    rows = compare_fixtures(fixtures, baseline_provider=baseline, ollama_provider=ollama)

    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "example"
    assert row["label_match_baseline"] is True
    assert row["label_match_ollama"] is False
    assert row["ollama_failed_or_fell_back"] is False
    assert row["snippet_quality"] == ""
    assert row["driver_quality"] == ""
    assert row["research_only"] == ""
    assert row["review_notes"] == ""


def test_write_reports_creates_csv_and_markdown(tmp_path) -> None:
    rows = [
        {
            "id": "example",
            "ticker": "AMD",
            "title": "AMD example",
            "expected_label": "positive",
            "expected_score_min": 0.2,
            "expected_score_max": 1.0,
            "expected_drivers": '["guidance"]',
            "baseline_provider": "baseline",
            "baseline_label": "positive",
            "baseline_score": 0.5,
            "baseline_confidence": 0.7,
            "baseline_drivers": '["guidance"]',
            "baseline_evidence_snippets": '["AMD raised guidance."]',
            "baseline_limitations": "[]",
            "baseline_runtime_seconds": 0.01,
            "label_match_baseline": True,
            "ollama_provider": "ollama",
            "ollama_label": "mixed",
            "ollama_score": 0.1,
            "ollama_confidence": 0.6,
            "ollama_drivers": '["guidance", "valuation"]',
            "ollama_evidence_snippets": '["AMD raised guidance."]',
            "ollama_limitations": '["Single article."]',
            "ollama_runtime_seconds": 1.2,
            "ollama_error": "",
            "ollama_failed_or_fell_back": False,
            "ollama_native_label_match": False,
            "label_match_ollama": False,
            "snippet_quality": "",
            "driver_quality": "",
            "research_only": "",
            "review_notes": "",
            "review_action": "",
        }
    ]

    csv_path, markdown_path, review_path = write_reports(rows, tmp_path)

    assert csv_path.read_text(encoding="utf-8").startswith("id,ticker,title")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Sentiment Provider Comparison" in markdown
    assert "Baseline label matches: 1/1" in markdown
    assert "Ollama native label matches: 0/1" in markdown
    assert "Ollama or fallback label matches: 0/1" in markdown
    review = review_path.read_text(encoding="utf-8")
    assert "# Sentiment Provider Qualitative Review" in review
    assert "## example" in review
    assert "- Snippet quality: " in review
    assert "- Driver quality: " in review
    assert "- Research-only: " in review
    assert "- Review action: " in review


def test_compare_fixtures_leaves_ollama_match_blank_when_ollama_not_run() -> None:
    fixtures = [
        {
            "id": "example",
            "ticker": "AMD",
            "title": "AMD example",
            "text": "AMD raised guidance.",
            "expected_label": "positive",
            "expected_drivers": ["guidance"],
        }
    ]
    baseline = FakeProvider(
        SentimentResult(
            label="positive",
            score=0.5,
            confidence=0.7,
            drivers=["guidance"],
            evidence_snippets=["AMD raised guidance."],
            limitations=[],
            provider="baseline",
            model_name="baseline",
            model_version="test",
        )
    )

    rows = compare_fixtures(fixtures, baseline_provider=baseline)

    assert rows[0]["ollama_provider"] == ""
    assert rows[0]["ollama_native_label_match"] == ""
    assert rows[0]["label_match_ollama"] == ""


def test_select_fixtures_filters_by_fixture_ids_in_fixture_order() -> None:
    fixtures = [
        {"id": "first"},
        {"id": "second"},
        {"id": "third"},
    ]

    selected = select_fixtures(fixtures, fixture_ids=["third", "first"])

    assert [fixture["id"] for fixture in selected] == ["first", "third"]


def test_select_fixtures_applies_limit_after_filtering() -> None:
    fixtures = [
        {"id": "first"},
        {"id": "second"},
        {"id": "third"},
    ]

    selected = select_fixtures(fixtures, fixture_ids=["first", "third"], limit=1)

    assert [fixture["id"] for fixture in selected] == ["first"]


def test_select_fixtures_rejects_unknown_fixture_id() -> None:
    with pytest.raises(ValueError, match="missing"):
        select_fixtures([{"id": "first"}], fixture_ids=["missing"])


def test_build_ollama_provider_can_disable_fallback_and_override_runtime_settings() -> None:
    provider = build_ollama_provider(
        Settings(
            OLLAMA_BASE_URL="http://localhost:11434/api",
            OLLAMA_SENTIMENT_MODEL="llama3.1:8b",
            OLLAMA_TIMEOUT_SECONDS=30,
            SENTIMENT_PROVIDER_FALLBACK="baseline",
            _env_file=None,
        ),
        fallback_enabled=False,
        base_url="http://localhost:11435/api",
        model="llama3.2:3b",
        timeout_seconds=12,
    )

    assert provider.base_url == "http://localhost:11435/api"
    assert provider.model == "llama3.2:3b"
    assert provider.timeout_seconds == 12
    assert provider.fallback_provider is None


def test_build_ollama_provider_uses_baseline_fallback_when_enabled() -> None:
    provider = build_ollama_provider(
        Settings(SENTIMENT_PROVIDER_FALLBACK="baseline", _env_file=None),
        fallback_enabled=True,
    )

    assert isinstance(provider.fallback_provider, BaselineSentimentProvider)
