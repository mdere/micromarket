# micromarket Model Quality Plan

## Goal

Move from a deterministic lexical sentiment baseline toward measured, evidence-backed sentiment models that improve analysis quality without breaking local-first operation or research-only guardrails.

The first modeling milestone is better article sentiment. Forecast improvements should come after sentiment quality, evidence extraction, and confidence calibration are measurable.

Before model quality can be trusted, every run must be time-aligned. Historical articles should be evaluated as if the system were standing at the article's publication time, not the later ingestion time.

## Current Baseline

The current backend uses `BaselineSentimentProvider`, a deterministic lexicon-based provider. It is useful because it is repeatable, offline, easy to test, transparent, and good enough to validate persistence, lineage, aggregation, forecast plumbing, and evaluation flow.

It is not expected to be accurate enough for final research use.

## Target Sentiment Output

Every sentiment provider should return the same stable contract:

- `sentiment_label`: `positive`, `neutral`, `negative`, or `mixed`,
- `sentiment_score`: normalized `-1.0` to `1.0`,
- `confidence_score`: `0.0` to `1.0`,
- `drivers`: short structured factors such as `earnings`, `guidance`, `demand`, `regulatory`, `valuation`, `macro`, or `analyst_action`,
- `evidence_snippets`: article excerpts that justify the label,
- `limitations`: model caveats for the article.

The provider must not output buy/sell/hold advice.

## As-Of Time Requirement

Every analysis should have an `analysis_as_of` timestamp that represents the decision point for the run.

For live analysis, `analysis_as_of` is the current analysis time. For historical replay, backtesting, and training examples, `analysis_as_of` should be derived from the article's `published_at` timestamp or an explicit user-provided historical timestamp.

All model inputs and targets must be relative to `analysis_as_of`:

- article evidence must have been published at or before `analysis_as_of`,
- market features must use only prices and indicators available at or before `analysis_as_of`,
- lookback windows, such as 30 days of price history, must end at `analysis_as_of`,
- forecast target windows must start at `analysis_as_of`,
- outcomes must measure prices after the forecast horizon, not prices already known at analysis time.

Example:

```text
today: 2026-04-01
ticker: AMD
article published_at: 2026-03-05
analysis_as_of: 2026-03-05
market lookback: approximately 30 days before 2026-03-05
forecast target: 2026-03-05 + next_close / 3 trading days / 7 trading days
outcome: actual market price at each target end
```

This rule prevents lookahead bias. A model should never receive market movement, article metadata, or outcome data that would not have been available at the simulated decision point.

## Recommended Model Progression

### Stage 0: Add Time-Aligned Historical Replay

Add the data and service semantics needed to run analyses against historical article dates before expanding model complexity.

Acceptance criteria:

- Analysis records store an `analysis_as_of` timestamp and source, such as `live`, `article_published_at`, or `manual_historical`.
- Market data provider interfaces can fetch historical lookback windows ending at `analysis_as_of`.
- Forecast runs store feature-window start/end timestamps and target-window start/end timestamps.
- Tests cover a historical article dated before the ingestion date and verify the forecast target starts from the historical date.

### Stage 1: Strengthen The Baseline

Improve the current deterministic provider before adding a neural or LLM model:

- expand finance-specific positive/negative lexicons,
- add driver tags,
- add phrase handling for negation and uncertainty,
- detect mixed articles,
- improve confidence scoring based on signal density and article length,
- add regression fixtures for known article examples.

Acceptance criteria:

- Existing tests remain deterministic and offline.
- New fixtures cover positive, negative, neutral, mixed, and weak-evidence articles.
- Provider version increments, for example `lexicon-baseline-v0.2`.

### Stage 2: Add Local LLM Sentiment Provider With Ollama

Add an optional `OllamaSentimentProvider` behind the existing `SentimentProvider` protocol.

Ollama should be treated as a local external provider:

- default base URL: `http://localhost:11434/api`,
- endpoint: `/chat`,
- JSON output required,
- timeout and failure behavior explicit,
- provider disabled unless configured,
- tests use fake provider responses and never require Ollama to be running.

The prompt should ask only for structured sentiment analysis and evidence extraction. It should not ask for trading decisions.

Suggested response schema:

```json
{
  "label": "positive",
  "score": 0.42,
  "confidence": 0.68,
  "drivers": ["earnings", "demand"],
  "evidence_snippets": ["..."],
  "limitations": ["Single article; sentiment may not represent broader market narrative."]
}
```

Acceptance criteria:

- Provider is selected by configuration, not hardcoded.
- Raw model output is stored as an artifact or structured debug payload when practical.
- Invalid JSON, missing fields, and provider timeouts return clear errors or fall back according to explicit configuration.
- Sentiment runs store provider/model name/version.

### Stage 3: Notebook Evaluation Harness

Use notebooks to compare providers against curated examples and later against forecast outcomes.

Start with a small local dataset:

- 20-50 article examples,
- multiple tickers,
- article `published_at` and expected `analysis_as_of` values,
- hand-labeled expected sentiment,
- expected drivers where obvious,
- examples with irrelevant ticker articles,
- examples with mixed or uncertain tone.

Metrics:

- label agreement against hand labels,
- mean absolute score error where hand scores exist,
- driver coverage,
- evidence snippet quality,
- confidence calibration by bucket,
- downstream forecast effect after enough outcomes exist.

Stable scoring logic must move into tested backend modules before the API depends on it.

### Stage 4: Optional Hosted Research Environments

Hosted notebooks can accelerate experiments, but they should not become MVP runtime dependencies.

Use Google Colab when local CPU is too slow for transformer experiments, a short GPU-backed notebook experiment is enough, and data can be exported safely without secrets or personal financial context.

Use Databricks only when datasets become large enough to justify a lakehouse/notebook workflow, collaborative ML tracking or larger experiment management is needed, and cost/setup overhead are justified.

Any hosted workflow must:

- use exported, sanitized datasets,
- avoid production secrets,
- avoid personal financial context,
- write findings back as code, tests, model artifacts, or reports in this repository.

## Provider Selection

Recommended configuration shape:

```text
SENTIMENT_PROVIDER=baseline
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_SENTIMENT_MODEL=llama3.1:8b
SENTIMENT_PROVIDER_FALLBACK=baseline
```

Provider selection should happen in `app/sentiment/dependencies.py`.

## First Implementation Slice

1. Add curated sentiment fixture data under `services/api/tests/fixtures` or `data/samples`.
2. Improve `BaselineSentimentProvider` to produce better drivers, mixed labels, and confidence.
3. Add tests for the curated examples.
4. Update model version strings.
5. Add notebook cells for comparing baseline output against fixtures.

## Second Implementation Slice

1. Add `OllamaSentimentProvider`.
2. Add configuration settings.
3. Add fake-provider tests for success, invalid JSON, timeout/failure, and fallback behavior.
4. Add README setup notes for local Ollama usage.
5. Add a notebook for comparing baseline vs Ollama output on the fixture set.

## Guardrails

- Keep the MVP local-first.
- Keep model outputs research-only.
- Preserve article, sentiment, forecast, provider, and model lineage.
- Do not use notebooks as production runtime.
- Do not commit model credentials, hosted notebook tokens, exported private data, or personal financial context.
- Prefer measured improvement over subjective prompt tweaking.
