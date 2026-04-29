from app.sentiment.comparison import compare_fixtures, write_reports
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
            "label_match_ollama": False,
            "snippet_quality": "",
            "driver_quality": "",
            "research_only": "",
            "review_notes": "",
            "review_action": "",
        }
    ]

    csv_path, markdown_path = write_reports(rows, tmp_path)

    assert csv_path.read_text(encoding="utf-8").startswith("id,ticker,title")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Sentiment Provider Comparison" in markdown
    assert "Baseline label matches: 1/1" in markdown
    assert "Ollama label matches: 0/1" in markdown
