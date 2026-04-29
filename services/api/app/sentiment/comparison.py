import argparse
import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.sentiment.baseline import BaselineSentimentProvider
from app.sentiment.ollama_provider import OllamaSentimentProvider
from app.sentiment.provider import SentimentProvider, SentimentProviderError, SentimentResult


REPO_ROOT = Path(__file__).resolve().parents[4]
API_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_PATH = API_ROOT / "tests" / "fixtures" / "sentiment_curated_examples.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "reports"


@dataclass(frozen=True)
class ProviderOutcome:
    result: SentimentResult | None
    runtime_seconds: float
    error: str | None = None


def load_fixtures(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_fixtures(
    fixtures: list[dict[str, Any]],
    *,
    baseline_provider: SentimentProvider,
    ollama_provider: SentimentProvider | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for fixture in fixtures:
        baseline = _score_provider(baseline_provider, fixture)
        ollama = _score_provider(ollama_provider, fixture) if ollama_provider is not None else None
        rows.append(_build_row(fixture, baseline=baseline, ollama=ollama))
    return rows


def write_reports(rows: list[dict[str, Any]], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "sentiment_provider_comparison.csv"
    markdown_path = output_dir / "sentiment_provider_comparison.md"
    _write_csv(rows, csv_path)
    _write_markdown(rows, markdown_path)
    return csv_path, markdown_path


def build_ollama_provider(settings: Settings) -> OllamaSentimentProvider:
    fallback_provider = (
        BaselineSentimentProvider()
        if (settings.sentiment_provider_fallback or "").strip().lower() == "baseline"
        else None
    )
    return OllamaSentimentProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_sentiment_model,
        timeout_seconds=settings.ollama_timeout_seconds,
        fallback_provider=fallback_provider,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare baseline and optional Ollama sentiment providers on curated fixtures."
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=DEFAULT_FIXTURE_PATH,
        help=f"Fixture JSON path. Defaults to {DEFAULT_FIXTURE_PATH}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for CSV/Markdown reports. Defaults to {DEFAULT_OUTPUT_DIR}.",
    )
    parser.add_argument(
        "--include-ollama",
        action="store_true",
        help="Also call the configured local Ollama sentiment provider.",
    )
    args = parser.parse_args()

    settings = Settings()
    baseline_provider = BaselineSentimentProvider()
    ollama_provider = build_ollama_provider(settings) if args.include_ollama else None
    rows = compare_fixtures(
        load_fixtures(args.fixtures),
        baseline_provider=baseline_provider,
        ollama_provider=ollama_provider,
    )
    csv_path, markdown_path = write_reports(rows, args.output_dir)
    print(f"Wrote {csv_path}")
    print(f"Wrote {markdown_path}")


def _score_provider(provider: SentimentProvider | None, fixture: dict[str, Any]) -> ProviderOutcome:
    if provider is None:
        return ProviderOutcome(result=None, runtime_seconds=0)
    start = time.perf_counter()
    try:
        result = provider.score_article(fixture["text"], ticker=fixture["ticker"])
        return ProviderOutcome(result=result, runtime_seconds=time.perf_counter() - start)
    except SentimentProviderError as exc:
        return ProviderOutcome(result=None, runtime_seconds=time.perf_counter() - start, error=str(exc))


def _build_row(
    fixture: dict[str, Any],
    *,
    baseline: ProviderOutcome,
    ollama: ProviderOutcome | None,
) -> dict[str, Any]:
    baseline_result = baseline.result
    ollama_result = ollama.result if ollama is not None else None
    expected_label = fixture["expected_label"]
    expected_drivers = fixture.get("expected_drivers", [])
    return {
        "id": fixture["id"],
        "ticker": fixture["ticker"],
        "title": fixture.get("title", ""),
        "expected_label": expected_label,
        "expected_score_min": fixture.get("expected_score_min", ""),
        "expected_score_max": fixture.get("expected_score_max", ""),
        "expected_drivers": _json(expected_drivers),
        "baseline_provider": baseline_result.provider if baseline_result else "",
        "baseline_label": baseline_result.label if baseline_result else "",
        "baseline_score": baseline_result.score if baseline_result else "",
        "baseline_confidence": baseline_result.confidence if baseline_result else "",
        "baseline_drivers": _json(baseline_result.drivers if baseline_result else []),
        "baseline_evidence_snippets": _json(
            baseline_result.evidence_snippets if baseline_result else []
        ),
        "baseline_limitations": _json(baseline_result.limitations if baseline_result else []),
        "baseline_runtime_seconds": round(baseline.runtime_seconds, 3),
        "label_match_baseline": baseline_result.label == expected_label if baseline_result else False,
        "ollama_provider": ollama_result.provider if ollama_result else "",
        "ollama_label": ollama_result.label if ollama_result else "",
        "ollama_score": ollama_result.score if ollama_result else "",
        "ollama_confidence": ollama_result.confidence if ollama_result else "",
        "ollama_drivers": _json(ollama_result.drivers if ollama_result else []),
        "ollama_evidence_snippets": _json(ollama_result.evidence_snippets if ollama_result else []),
        "ollama_limitations": _json(ollama_result.limitations if ollama_result else []),
        "ollama_runtime_seconds": round(ollama.runtime_seconds, 3) if ollama else "",
        "ollama_error": ollama.error if ollama and ollama.error else "",
        "ollama_failed_or_fell_back": _ollama_failed_or_fell_back(ollama_result, ollama),
        "label_match_ollama": ollama_result.label == expected_label if ollama_result else False,
        "snippet_quality": "",
        "driver_quality": "",
        "research_only": "",
        "review_notes": "",
        "review_action": "",
    }


def _ollama_failed_or_fell_back(
    result: SentimentResult | None,
    outcome: ProviderOutcome | None,
) -> bool | str:
    if outcome is None:
        return ""
    if outcome.error:
        return True
    return result is None or result.provider != "ollama"


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    label_matches = sum(1 for row in rows if row["label_match_baseline"])
    ollama_rows = [row for row in rows if row["ollama_provider"] or row["ollama_error"]]
    ollama_matches = sum(1 for row in ollama_rows if row["label_match_ollama"])
    lines = [
        "# Sentiment Provider Comparison",
        "",
        f"Fixture count: {len(rows)}",
        f"Baseline label matches: {label_matches}/{len(rows)}",
    ]
    if ollama_rows:
        lines.append(f"Ollama label matches: {ollama_matches}/{len(ollama_rows)}")
    lines.extend(
        [
            "",
            "| id | expected | baseline | ollama | baseline score | ollama score | review notes |",
            "| --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {id} | {expected_label} | {baseline_label} | {ollama_label} | "
            "{baseline_score} | {ollama_score} |  |".format(**row)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


if __name__ == "__main__":
    main()
