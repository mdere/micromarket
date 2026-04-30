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


def select_fixtures(
    fixtures: list[dict[str, Any]],
    *,
    fixture_ids: list[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    selected = fixtures
    if fixture_ids:
        requested_ids = set(fixture_ids)
        available_ids = {fixture["id"] for fixture in fixtures}
        missing_ids = sorted(requested_ids - available_ids)
        if missing_ids:
            raise ValueError(f"Unknown fixture id(s): {', '.join(missing_ids)}")
        selected = [fixture for fixture in fixtures if fixture["id"] in requested_ids]
    if limit is not None:
        selected = selected[:limit]
    return selected


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


def write_reports(rows: list[dict[str, Any]], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "sentiment_provider_comparison.csv"
    markdown_path = output_dir / "sentiment_provider_comparison.md"
    review_path = output_dir / "sentiment_provider_review.md"
    _write_csv(rows, csv_path)
    _write_markdown(rows, markdown_path)
    _write_review_markdown(rows, review_path)
    return csv_path, markdown_path, review_path


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
    parser.add_argument(
        "--fixture-id",
        action="append",
        dest="fixture_ids",
        help="Only compare this fixture id. May be repeated.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only compare the first N fixtures after any fixture-id filtering.",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1.")

    settings = Settings()
    baseline_provider = BaselineSentimentProvider()
    ollama_provider = build_ollama_provider(settings) if args.include_ollama else None
    fixtures = load_fixtures(args.fixtures)
    try:
        selected_fixtures = select_fixtures(
            fixtures,
            fixture_ids=args.fixture_ids,
            limit=args.limit,
        )
    except ValueError as exc:
        parser.error(str(exc))
    rows = compare_fixtures(
        selected_fixtures,
        baseline_provider=baseline_provider,
        ollama_provider=ollama_provider,
    )
    csv_path, markdown_path, review_path = write_reports(rows, args.output_dir)
    print(f"Wrote {csv_path}")
    print(f"Wrote {markdown_path}")
    print(f"Wrote {review_path}")


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
        "label_match_ollama": ollama_result.label == expected_label if ollama_result else "",
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
    ollama_fallbacks = sum(1 for row in ollama_rows if row["ollama_failed_or_fell_back"] is True)
    lines = [
        "# Sentiment Provider Comparison",
        "",
        f"Fixture count: {len(rows)}",
        f"Baseline label matches: {label_matches}/{len(rows)}",
    ]
    if ollama_rows:
        lines.append(f"Ollama label matches: {ollama_matches}/{len(ollama_rows)}")
        lines.append(f"Ollama failures/fallbacks: {ollama_fallbacks}/{len(ollama_rows)}")
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


def _write_review_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Sentiment Provider Qualitative Review",
        "",
        "Use this worksheet to review provider quality in VS Code. Fill in the blank",
        "rubric fields after reading the expected label, drivers, snippets, and limitations.",
        "",
        "Rubric values:",
        "",
        "- Snippet quality: `pass`, `partial`, or `fail`.",
        "- Driver quality: `pass`, `partial`, or `fail`.",
        "- Research-only: `pass` or `fail`.",
        "- Review action: `fixture_ok`, `expand_fixture`, `tune_prompt`, `tune_parser`, `provider_bug`, or `no_action`.",
        "",
    ]
    for row in rows:
        lines.extend(_review_section(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _review_section(row: dict[str, Any]) -> list[str]:
    return [
        f"## {row['id']}",
        "",
        f"Ticker: `{row['ticker']}`",
        f"Title: {row['title']}",
        "",
        "Expected:",
        "",
        f"- Label: `{row['expected_label']}`",
        f"- Score range: `{row['expected_score_min']}` to `{row['expected_score_max']}`",
        f"- Drivers: {_format_json_list(row['expected_drivers'])}",
        "",
        "Baseline:",
        "",
        f"- Label: `{row['baseline_label']}`",
        f"- Score: `{row['baseline_score']}`",
        f"- Confidence: `{row['baseline_confidence']}`",
        f"- Label match: `{row['label_match_baseline']}`",
        f"- Drivers: {_format_json_list(row['baseline_drivers'])}",
        f"- Evidence snippets: {_format_json_list(row['baseline_evidence_snippets'])}",
        f"- Limitations: {_format_json_list(row['baseline_limitations'])}",
        f"- Runtime seconds: `{row['baseline_runtime_seconds']}`",
        "",
        "Ollama:",
        "",
        f"- Provider: `{row['ollama_provider']}`",
        f"- Label: `{row['ollama_label']}`",
        f"- Score: `{row['ollama_score']}`",
        f"- Confidence: `{row['ollama_confidence']}`",
        f"- Label match: `{row['label_match_ollama']}`",
        f"- Failed or fell back: `{row['ollama_failed_or_fell_back']}`",
        f"- Error: `{row['ollama_error']}`",
        f"- Drivers: {_format_json_list(row['ollama_drivers'])}",
        f"- Evidence snippets: {_format_json_list(row['ollama_evidence_snippets'])}",
        f"- Limitations: {_format_json_list(row['ollama_limitations'])}",
        f"- Runtime seconds: `{row['ollama_runtime_seconds']}`",
        "",
        "Review:",
        "",
        "- Snippet quality: ",
        "- Driver quality: ",
        "- Research-only: ",
        "- Review action: ",
        "- Review notes: ",
        "",
    ]


def _format_json_list(value: Any) -> str:
    if not value:
        return "`[]`"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return f"`{value}`"
    else:
        parsed = value
    if not parsed:
        return "`[]`"
    if not isinstance(parsed, list):
        return f"`{parsed}`"
    return "\n  - " + "\n  - ".join(str(item) for item in parsed)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


if __name__ == "__main__":
    main()
