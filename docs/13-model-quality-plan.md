# micromarket Model Quality Plan

## Goal

Move from a deterministic lexical sentiment baseline toward measured, evidence-backed sentiment models that improve analysis quality without breaking local-first operation or research-only guardrails.

The first modeling milestone is better article sentiment. Forecast improvements should come after sentiment quality, evidence extraction, and confidence calibration are measurable.

Before model quality can be trusted, every run must be time-aligned and backed by stable ticker context. Historical articles should be evaluated as if the system were standing at the article's publication time, not the later ingestion time.

See `docs/14-ticker-context-ingestion-plan.md` for the prerequisite ticker onboarding, market-history backfill, and related-entity extraction foundation.

## Current Baseline

The current backend uses `BaselineSentimentProvider`, a deterministic lexicon-based provider. It is useful because it is repeatable, offline, easy to test, transparent, and good enough to validate persistence, lineage, aggregation, forecast plumbing, and evaluation flow.

It is not expected to be accurate enough for final research use.

Current baseline version: `sentiment-lexicon-baseline` `0.2.0`.

The curated fixture set lives at `services/api/tests/fixtures/sentiment_curated_examples.json` and currently includes 20 examples covering positive, negative, neutral, mixed, weak-evidence, negated-positive, analyst-action, regulatory/product, supply-chain, related-entity, uncertainty, guidance-cut, and irrelevant-ticker cases. The baseline now emits finance-specific driver categories, detects mixed positive/negative articles, handles simple negation, and lowers confidence for uncertainty language. Continue expanding the fixture set whenever a new failure case appears.

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

### Stage 0: Add Ticker Context And Time-Aligned Historical Replay

Add the data and service semantics needed to run analyses against historical article dates before expanding model complexity.

Acceptance criteria:

- New tickers can trigger a configurable market-history backfill, such as 30 days.
- Analysis records store an `analysis_as_of` timestamp and source, such as `live`, `article_published_at`, or `manual_historical`.
- Market data provider interfaces can fetch historical lookback windows ending at `analysis_as_of`.
- Forecast runs store feature-window start/end timestamps and target-window start/end timestamps.
- Articles can store extracted related entities and keywords for later narrative analysis.
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
- New fixtures cover positive, negative, neutral, mixed, and weak-evidence articles. Expanded fixture set is implemented with 20 examples.
- Provider version increments, for example `lexicon-baseline-v0.2`. Current implemented version is `0.2.0`.

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

- Provider is selected by configuration, not hardcoded. Done with `SENTIMENT_PROVIDER`.
- Raw model output is stored as an artifact or structured debug payload when practical. Not yet implemented; revisit after initial provider comparisons.
- Invalid JSON, missing fields, and provider timeouts return clear errors or fall back according to explicit configuration. Done with `SENTIMENT_PROVIDER_FALLBACK`.
- Sentiment runs store provider/model name/version. Done through the shared `SentimentProvider` contract.

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

### Baseline Vs Ollama Comparison Workflow

The comparison should answer a narrow question first: does Ollama produce more useful, evidence-grounded article sentiment than the deterministic baseline on the curated fixture set, without breaking local-first reliability or research-only language?

Run the comparison in phases:

1. **Smoke test provider plumbing**
   - Confirm `SENTIMENT_PROVIDER=ollama` returns `provider: "ollama"` in `sentiment_runs`.
   - Confirm timeout/fallback behavior is visible in `limitations` when Ollama is too slow or unavailable.
   - Tune only operational settings here, such as `OLLAMA_TIMEOUT_SECONDS`; do not change prompts based on one example.

2. **Fixture comparison**
   - Use `services/api/tests/fixtures/sentiment_curated_examples.json` as the first labeled dataset.
   - Run `notebooks/02_sentiment_baseline.ipynb` with `RUN_OLLAMA_COMPARISON = True`.
  - Or run `cd services/api && python -m app.sentiment.comparison --include-ollama` to write CSV/Markdown reports under `data/reports`.
  - For slow local CPU runs, use `--limit N` or one or more `--fixture-id ID` arguments to compare a smaller batch before running the full fixture set.
   - Record per-example baseline and Ollama label, score, confidence, drivers, evidence snippets, limitations, runtime, and failures/fallbacks.
   - Expand the fixture set whenever either provider fails in an interesting way.

3. **Qualitative review**
   - Read the evidence snippets, not only the label.
   - Mark whether snippets actually justify the sentiment.
   - Mark whether drivers are specific enough to be useful, such as `guidance` or `valuation`, rather than vague.
   - Reject outputs that drift into direct investment advice or unsupported claims, even if the label is correct.
   - Write a short review note for each mismatch or suspicious pass so the fixture can teach the next prompt/provider change.

4. **Quantitative review**
   - Compute label accuracy against hand labels.
   - Compute macro accuracy by label so neutral/mixed examples are not hidden by positive/negative examples.
   - Compute mean absolute score error once fixtures include expected score ranges or hand scores.
   - Track invalid JSON rate, fallback rate, and median/p95 runtime.
   - Track driver coverage: how often expected drivers appear in provider output.

5. **Decision checkpoint**
   - Keep `baseline` as default until Ollama beats baseline on label accuracy, snippet quality, and driver usefulness by a meaningful margin.
   - Keep fallback enabled for local use unless Ollama runtime is consistently reliable.
   - Promote prompt or parsing improvements into provider tests before depending on them in the API.
   - Do not let a better single example override fixture-level results.

Suggested comparison table columns:

```text
id
ticker
expected_label
baseline_label
ollama_label
baseline_score
ollama_score
baseline_confidence
ollama_confidence
label_match_baseline
label_match_ollama
expected_drivers
baseline_drivers
ollama_drivers
ollama_runtime_seconds
ollama_failed_or_fell_back
review_notes
```

The report generator writes this review surface to:

```text
data/reports/sentiment_provider_comparison.csv
data/reports/sentiment_provider_comparison.md
data/reports/sentiment_provider_review.md
```

The CSV is useful for spreadsheet-style review. The review Markdown is easier to read in VS Code because it creates one section per fixture with blank rubric fields. Keep generated reports local unless a specific report becomes useful as documentation; `data/reports/**` is ignored by Git by default.

Initial decision thresholds before changing defaults:

- At least 20 curated examples across positive, negative, neutral, mixed, weak-evidence, irrelevant-ticker, uncertainty, and negation cases. Current count is 20, which is enough for the first small comparison baseline.
- Ollama label accuracy is better than baseline by at least 10 percentage points, or it materially improves mixed/neutral cases without hurting positive/negative cases.
- Ollama evidence snippets are judged useful on at least 80% of examples.
- Invalid JSON and fallback rate are low enough for local research use.
- Runtime is acceptable for the local machine, or slow enough that it remains an explicit experimental provider.

#### Qualitative Review Example

Use qualitative review to inspect whether the provider's reasoning is grounded in the article, not merely whether the final label matches the hand label.

Example fixture:

```json
{
  "id": "mixed_growth_valuation_uncertainty",
  "ticker": "NVDA",
  "expected_label": "mixed",
  "expected_drivers": ["demand", "earnings", "uncertainty", "valuation"],
  "text": "NVDA shares advanced after strong data-center demand and revenue growth, but analysts also highlighted valuation concerns, supply constraints, and rate uncertainty. The article described upside from HBM adoption while noting limited conviction."
}
```

Example provider output:

```json
{
  "label": "positive",
  "score": 0.64,
  "confidence": 0.76,
  "drivers": ["demand", "earnings", "product"],
  "evidence_snippets": [
    "NVDA shares advanced after strong data-center demand and revenue growth",
    "The article described upside from HBM adoption"
  ],
  "limitations": ["Single article."]
}
```

Review:

```text
label_match: no
snippet_quality: partial
driver_quality: partial
research_only: pass
review_notes:
  Output captures the positive demand/earnings/product evidence, but misses the
  valuation, supply, uncertainty, and limited-conviction language. Label should
  be mixed, not positive, because the article contains explicit offsetting risk
  signals. Evidence snippets are real article excerpts, but they selectively
  quote only the positive side.
action:
  Add or keep this as a mixed fixture. Consider prompt language that asks for
  both supporting and offsetting evidence before assigning the label. Do not
  change default provider behavior based on this single case.
```

The same example with a stronger output:

```json
{
  "label": "mixed",
  "score": 0.15,
  "confidence": 0.7,
  "drivers": ["demand", "earnings", "valuation", "supply", "uncertainty", "product"],
  "evidence_snippets": [
    "strong data-center demand and revenue growth",
    "valuation concerns, supply constraints, and rate uncertainty",
    "upside from HBM adoption while noting limited conviction"
  ],
  "limitations": ["Single article; sentiment may not represent the broader market narrative."]
}
```

Review:

```text
label_match: yes
snippet_quality: pass
driver_quality: pass
research_only: pass
review_notes:
  Output captures both positive and negative evidence. Mixed label is justified,
  score is near neutral but slightly positive, and snippets are grounded in the
  fixture text. This is a useful response for the research workflow.
action:
  Count as a qualitative pass. If repeated across fixtures, this supports
  trusting the provider for mixed-evidence articles.
```

Use this simple rubric for each example:

```text
label_match:
  yes / no / debatable

snippet_quality:
  pass = snippets directly support the label and include important opposing evidence when present
  partial = snippets are real but incomplete or one-sided
  fail = snippets are missing, generic, hallucinated, or unrelated

driver_quality:
  pass = drivers match important article themes and expected drivers
  partial = drivers are plausible but incomplete or too broad
  fail = drivers are unsupported or miss the central signal

research_only:
  pass = no direct investment advice
  fail = contains buy/sell/hold instruction, personalized advice, or unsupported forecast claim

action:
  fixture_ok / expand_fixture / tune_prompt / tune_parser / provider_bug / no_action
```

When reviewing, look for suspicious passes. A provider can get the label right for the wrong reason. For example, an output that labels an article `negative` because of "market crash risk" fails qualitative review if the article only mentioned a mild guidance cut and never discussed a crash.

### First Expanded Comparison Run

Run date: 2026-04-30.

Command:

```bash
cd services/api
python -m app.sentiment.comparison --include-ollama
```

Configuration notes:

- Fixture count: 19.
- Ollama model: configured local `OLLAMA_SENTIMENT_MODEL`.
- `OLLAMA_TIMEOUT_SECONDS` was high enough for the full run to complete, but three rows still fell back to baseline after timeout.
- Generated reports are local ignored artifacts under `data/reports`.

Results:

| Metric | Baseline | Ollama |
| --- | ---: | ---: |
| Label matches | 16/19 | 18/19 |
| Fallbacks/timeouts | n/a | 3/19 |
| Expected-driver coverage | 54/58 | 30/58 |
| Rows with all expected drivers covered | 10/14 | 2/14 |
| Runtime | near-instant | 90.7s min / 129.2s avg / 180.0s max |

Interpretation:

- Ollama improved label accuracy on this expanded fixture set, especially for cases that the lexical baseline mishandled:
  - `irrelevant_positive_other_ticker`: baseline over-read positive NVDA language for AMD; Ollama correctly returned neutral.
  - `negative_analyst_downgrade`: baseline softened the article to mixed; Ollama correctly returned negative.
  - `uncertain_possible_guidance_pressure`: baseline softened the article to mixed; Ollama correctly returned negative.
- Ollama still missed one hand label:
  - `mixed_partner_strength_customer_delay`: expected mixed, Ollama returned negative. It captured supply/uncertainty risks but underweighted positive demand/backlog/upside language.
- Ollama's main weakness is structured driver coverage, not label selection. It often returns plausible but incomplete drivers, and sometimes introduces broad or unsupported drivers such as `valuation`.
- Runtime is still too slow for default API behavior on the current local CPU path. Keep Ollama optional and keep fallback enabled.
- Three timeouts/fallbacks mean reported Ollama quality should be treated cautiously until runtime is more stable or the report can run in smaller batches.

Recommended next actions:

1. Add at least one more fixture to reach the initial 20-example threshold.
2. Add batch controls to the report generator, such as `--limit` or `--fixture-id`, so local CPU runs can be reviewed incrementally.
3. Tune the Ollama prompt for driver extraction:
   - require all materially relevant expected driver categories,
   - require both positive and negative drivers for mixed articles,
   - forbid unsupported driver categories,
   - ask for uncertainty language when it affects confidence.
4. Keep `baseline` as the default provider for now. Ollama is promising for labels but not yet reliable enough on runtime and structured drivers.

### First Follow-Up Prompt And Batching Slice

Implemented after reviewing the first expanded comparison:

- Fixture count increased from 19 to 20 with `mixed_earnings_beat_guidance_cut`, which covers an earnings beat offset by cut guidance, cautious demand, margin pressure, product adoption, and uncertainty.
- The report generator now supports smaller local comparison runs:
  - `python -m app.sentiment.comparison --include-ollama --limit 5`
  - `python -m app.sentiment.comparison --include-ollama --fixture-id mixed_partner_strength_customer_delay`
  - `python -m app.sentiment.comparison --include-ollama --fixture-id mixed_partner_strength_customer_delay --fixture-id mixed_earnings_beat_guidance_cut`
- The report generator also supports runtime diagnosis without editing `.env`:
  - `--ollama-no-fallback` makes native Ollama errors visible instead of substituting baseline output,
  - `--ollama-timeout-seconds N` changes the timeout for that comparison run,
  - `--ollama-model MODEL` and `--ollama-base-url URL` override local Ollama settings for that comparison run.
- The Ollama prompt now explicitly asks for grounded driver coverage:
  - include every materially relevant supported driver,
  - include both supportive and offsetting drivers for mixed labels,
  - do not include a driver unless an evidence snippet supports it,
  - use `uncertainty`, `analyst_action`, and `guidance` for the relevant language.

Single-fixture no-fallback runs on `mixed_earnings_beat_guidance_cut` reached Ollama after about 244.7 seconds and 265.5 seconds, but the provider rejected the responses because list fields did not always match the strict `list[str]` schema. That is progress over timeout-only failures: the local path can produce responses, but runtime remains very slow and schema compliance is fragile. The parser now tolerates common list-field variants while preserving the structured provider contract internally: single strings become one-item lists, comma-separated driver strings become driver lists, and driver objects with `driver`, `category`, `name`, or `type` keys become plain driver strings.

The next single-fixture no-fallback run produced the first valid native Ollama row after about 263.1 seconds. Ollama matched the expected `mixed` label with score `-0.33`, returned grounded snippets, stayed research-only, and covered `earnings`, `guidance`, `demand`, and `uncertainty`. It missed the expected `product` driver, so qualitative assessment is snippet quality `pass`, driver quality `partial`, research-only `pass`. Runtime remains much too slow for default API behavior on the current local CPU path. The parser now also strips extra wrapping quote characters from evidence snippets.

Next review step: rerun the two mixed fixtures with `--ollama-no-fallback`, inspect native label quality, driver coverage, snippets, and runtime, then decide whether to try a larger batch or first reduce runtime with a smaller local model.

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

1. Add ticker market-history backfill and `analysis_as_of` semantics.
2. Add related-entity extraction and article/entity lineage.
3. Add curated sentiment fixture data under `services/api/tests/fixtures` or `data/samples`. Done.
4. Improve `BaselineSentimentProvider` to produce better drivers, mixed labels, and confidence. Done for deterministic baseline `0.2.0`.
5. Add tests for the curated examples. Done.
6. Update model version strings. Done.
7. Add notebook cells for comparing baseline output against fixtures. Done in `notebooks/02_sentiment_baseline.ipynb`.

## Second Implementation Slice

1. Add `OllamaSentimentProvider`. Done.
2. Add configuration settings. Done.
3. Add fake-provider tests for success, invalid JSON, timeout/failure, and fallback behavior. Done.
4. Add README setup notes for local Ollama usage. Done.
5. Add a notebook for comparing baseline vs Ollama output on the fixture set. Initial optional notebook section added; expand during experiments.

## Third Implementation Slice

1. Add a sentiment provider comparison report generator. Done in `app/sentiment/comparison.py`.
2. Write CSV and Markdown reports under `data/reports`. Done.
3. Include blank human-review fields for snippet quality, driver quality, research-only check, review notes, and review action. Done.
4. Generate a VS Code-friendly per-fixture review Markdown worksheet. Done.
5. Use the report to expand fixtures and review provider quality before changing provider defaults. Initial 20-example floor is reached.
6. Promote repeated findings into provider tests and prompt/parser improvements. First driver-extraction prompt tune is implemented.

## Guardrails

- Keep the MVP local-first.
- Keep model outputs research-only.
- Preserve article, sentiment, forecast, provider, and model lineage.
- Do not use notebooks as production runtime.
- Do not commit model credentials, hosted notebook tokens, exported private data, or personal financial context.
- Prefer measured improvement over subjective prompt tweaking.
