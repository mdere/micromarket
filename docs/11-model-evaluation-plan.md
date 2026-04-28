# micromarket Model Evaluation Plan

## Goal

The MVP model should not only generate forecasts. It should make forecasts that can be measured later against real outcomes and simple baselines.

The evaluation goal is to learn whether article sentiment contributes useful signal beyond naive assumptions.

The next model-quality goal is to improve the data foundation first, then sentiment. Ticker market-history context, as-of-time alignment, and related-entity extraction should be in place before judging sentiment or forecast model quality.

See `docs/13-model-quality-plan.md` for the provider progression from deterministic baseline to optional Ollama/local LLM sentiment.

See `docs/14-ticker-context-ingestion-plan.md` for ticker onboarding, market-history backfill, and related-entity extraction.

## As-Of Time And Lookahead Bias

Forecast evaluation must be anchored to the analysis `analysis_as_of` timestamp.

For a live run, `analysis_as_of` is the current analysis time. For a historical article or training example, `analysis_as_of` should come from the article's `published_at` timestamp or an explicit historical timestamp.

All model inputs must be available at or before `analysis_as_of`:

- article evidence,
- market quote and historical price features,
- moving averages and momentum windows,
- sentiment aggregates,
- forecast baseline features.

All outcomes must occur after `analysis_as_of`.

Example:

```text
today: 2026-04-01
article published_at: 2026-03-05
analysis_as_of: 2026-03-05
market lookback: prior 30 days ending on 2026-03-05
3-trading-day target: starts on 2026-03-05 and ends after 3 trading days
```

This prevents lookahead bias. The model should not be rewarded for using price movement or articles that were not available at the simulated decision point.

## Initial Forecast Targets

Store forecasts for:

- next close,
- 3 trading days,
- 7 trading days.

Primary UI forecast:

- 3 trading days.

## Model Outputs To Evaluate

Each forecast should include:

- predicted direction,
- predicted percent change,
- confidence score,
- model version,
- horizon,
- top factors,
- evidence article ids,
- limitations,
- start price,
- feature window start and end,
- target evaluation time.

## Baselines

Compare every forecast against at least these baselines:

### No-Change Baseline

Prediction:

- percent change: `0`
- direction: `flat`

Purpose:

- Establish whether the model adds value beyond assuming no movement.

### Momentum Baseline

Prediction:

- direction and percent change based on recent price movement.

Purpose:

- Checks whether the model beats simple market momentum.

### Sentiment-Only Baseline

Prediction:

- direction derived only from aggregate sentiment score.

Purpose:

- Checks whether market metrics improve on raw sentiment.

## Metrics

### Directional Accuracy

Measures whether predicted direction matched actual direction.

Use for:

- up/down/flat correctness,
- comparison by horizon,
- comparison by confidence bucket.

### Mean Absolute Error

Measures average absolute difference between predicted percent change and actual percent change.

Use for:

- percent-change forecast quality,
- model-vs-baseline comparison.

### Confidence Calibration

Measures whether higher-confidence forecasts are actually more accurate.

Example buckets:

- 0.0-0.3 low confidence,
- 0.3-0.6 medium confidence,
- 0.6-0.8 high confidence,
- 0.8-1.0 very high confidence.

Expected result:

- higher confidence buckets should show higher accuracy or lower error.

### Evidence Strength Correlation

Measures whether forecasts supported by multiple aligned articles perform better than forecasts based on weak or conflicting evidence.

Signals:

- article count,
- included article count,
- sentiment agreement,
- source diversity,
- recency.

### Related Entity Signal

Measures whether articles mentioning related companies, products, partners, suppliers, customers, competitors, or themes have useful explanatory value for the primary ticker.

Use for:

- entity mention counts,
- entity sentiment by article,
- related-entity agreement or conflict,
- supplier/customer/competitor relationship type,
- price movement after articles involving the same entity or narrative.

### Sentiment Fixture Quality

Measures whether a sentiment provider can classify curated article examples before downstream forecast evaluation is possible.

Use for:

- label agreement against hand-labeled examples,
- score error against expected rough scores,
- driver extraction coverage,
- evidence snippet relevance,
- confidence reasonableness.

This is the first metric set for comparing the deterministic baseline against Ollama/local LLM output.

## MVP Success Thresholds

Early MVP success should not require production-grade accuracy. It should require measurable learning.

Minimum useful outcome:

- Forecast records are complete enough to evaluate.
- Confidence buckets show some relationship to correctness.
- Sentiment summaries are understandable and evidence-backed.
- Model can be compared to no-change and momentum baselines.

Stronger MVP outcome:

- 3-trading-day directional accuracy beats momentum baseline over a small test set.
- High-confidence forecasts outperform low-confidence forecasts.
- Forecast explanations match stored evidence.

## Evaluation Workflow

1. User runs analysis.
2. System resolves `analysis_as_of`.
3. System fetches market features ending at `analysis_as_of`.
4. System stores forecast records for all horizons.
5. System waits until target horizon passes.
6. User or scheduled job runs evaluation refresh.
7. System fetches actual end price.
8. System creates `forecast_outcomes`.
9. Evaluation summary updates aggregate metrics.

## Notebook-Assisted Evaluation

Jupyter notebooks are recommended for the MVP evaluation workflow because early model work will require fast inspection and iteration before logic is stable enough to become API code.

Use notebooks to:

- inspect whether `yfinance` quote/history data is usable for selected equities and ETFs,
- compare sentiment distributions across articles and tickers,
- compare baseline, Ollama/local LLM, FinBERT, or other experimental sentiment providers against the same curated fixture set,
- tune baseline forecast weights,
- inspect confidence calibration by bucket,
- compare the forecast model against no-change, momentum, and sentiment-only baselines,
- create charts and tables for local evaluation reports.

Notebook outputs should not be the system of record. Forecasts, outcomes, model versions, and provider metadata should remain in PostgreSQL. Reports or charts generated from notebooks can be stored under `data/reports`, while stable model logic should be promoted into tested backend modules.

Hosted notebooks such as Google Colab or Databricks can be used for exploratory model experiments when local hardware is insufficient. Export only sanitized datasets, do not include secrets or personal financial context, and promote useful results back into this repository as code, fixtures, tests, model artifacts, or reports.

## Evaluation API

### `POST /evaluations/refresh`

Finds forecasts whose target horizon has passed and no outcome exists.

Steps:

- Fetch actual price.
- Compute actual percent change.
- Compute actual direction.
- Compare against forecast.
- Compare against baselines.
- Store outcome.

### `GET /evaluations/summary`

Returns:

- total evaluated forecasts,
- accuracy by horizon,
- MAE by horizon,
- baseline comparison,
- confidence calibration,
- model version breakdown.

## Retrospective Questions

For each model iteration, answer:

- Did accuracy improve?
- Did explainability improve?
- Did confidence calibration improve?
- Did the model overreact to single articles?
- Did the model handle conflicting articles honestly?
- Did market metrics improve or dilute sentiment signal?

## Model Versioning

Every model change should increment a version string.

Recommended format:

```text
sentiment-lexicon-v0.1
sentiment-lexicon-v0.2
sentiment-ollama-llama3.1-8b-v0.1
forecast-rules-v0.1
forecast-rules-v0.2
```

Version changes should be recorded when any of these change:

- sentiment prompt,
- sentiment provider,
- sentiment scoring scale,
- forecast formula,
- feature weights,
- market-data provider,
- evidence-strength calculation.

## Initial Baseline Forecast Formula

Start with a transparent weighted score:

```text
forecast_score =
  sentiment_weight * aggregate_sentiment_score
  + agreement_weight * sentiment_agreement_score
  + evidence_weight * evidence_strength_score
  + momentum_weight * recent_momentum_score
  - volatility_penalty * volatility_score
```

Then map:

- score direction to `up`, `down`, `flat`, or `uncertain`,
- score magnitude to predicted percent change,
- evidence quality and agreement to confidence.

The exact weights should be documented in the model version parameters.

## Guardrails

- Low article count should reduce confidence.
- Conflicting sentiment should reduce confidence.
- Stale articles should reduce confidence.
- High volatility should reduce confidence.
- The model should be allowed to return `uncertain`.
- The UI should display limitations every time.

## First Evaluation Dataset

Start with a small repeatable set:

- 5-10 US equities.
- 2-3 ETFs.
- A mix of high-news and low-news tickers.
- Several manual article examples.
- Several URL-ingested article examples.

Do not judge model quality from one or two forecasts. Use early results to validate pipeline integrity first.
