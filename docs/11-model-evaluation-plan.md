# micromarket Model Evaluation Plan

## Goal

The MVP model should not only generate forecasts. It should make forecasts that can be measured later against real outcomes and simple baselines.

The evaluation goal is to learn whether article sentiment contributes useful signal beyond naive assumptions.

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
2. System stores forecast records for all horizons.
3. System waits until target horizon passes.
4. User or scheduled job runs evaluation refresh.
5. System fetches actual end price.
6. System creates `forecast_outcomes`.
7. Evaluation summary updates aggregate metrics.

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
sentiment-baseline-v0.1
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
