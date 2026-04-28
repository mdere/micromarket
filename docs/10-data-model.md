# micromarket Data Model

## Data Model Goals

The data model must preserve enough lineage to answer:

- What article evidence was used?
- What sentiment model produced the sentiment scores?
- What forecast model produced the forecast?
- What market data was available at forecast time?
- What timestamp did the analysis simulate or represent?
- What related entities, companies, products, or themes appeared in the article?
- What happened later?
- Did the model beat a naive baseline?

## Core Entities

## `assets`

Represents a tradable symbol such as a US equity or ETF.

Fields:

- `id`
- `symbol`
- `name`
- `asset_type`: `equity` or `etf`
- `exchange`
- `sector`
- `industry`
- `currency`
- `created_at`
- `updated_at`

Notes:

- Use `assets` rather than `companies` so ETFs fit cleanly.

## `market_quotes`

Stores market data snapshots used by analyses and forecasts.

Fields:

- `id`
- `asset_id`
- `provider`
- `price`
- `previous_close`
- `open`
- `day_high`
- `day_low`
- `volume`
- `market_cap`
- `fifty_two_week_high`
- `fifty_two_week_low`
- `moving_average_50`
- `moving_average_200`
- `beta`
- `pe_ratio`
- `quote_time`
- `retrieved_at`
- `raw_payload_artifact_path`

## `market_price_history`

Stores historical market prices used for lookback features, historical replay, and outcome evaluation.

Fields:

- `id`
- `asset_id`
- `provider`
- `price_date`
- `open`
- `high`
- `low`
- `close`
- `adjusted_close`
- `volume`
- `retrieved_at`
- `raw_payload_artifact_path`

Notes:

- Price history supports configurable ticker onboarding lookbacks, such as 30 days.
- Historical feature windows should read from this table when possible before making new provider calls.

## `ticker_contexts`

Stores local context and backfill state for a ticker workspace.

Fields:

- `id`
- `asset_id`
- `lookback_days`
- `history_start_date`
- `history_end_date`
- `provider`
- `last_backfilled_at`
- `created_at`
- `updated_at`

Notes:

- A ticker context is created or refreshed when a ticker is first analyzed or when history is missing for a requested `analysis_as_of`.
- The context should not replace analysis-level lineage; it provides reusable market context for repeated runs.

## `analyses`

Represents one user-triggered ticker analysis run.

Fields:

- `id`
- `asset_id`
- `status`: `created`, `running`, `completed`, `failed`
- `primary_horizon`: default `3_trading_days`
- `input_mode`: `manual_text`, `url`, `mixed`
- `analysis_as_of`
- `analysis_as_of_source`: `live`, `article_published_at`, `manual_historical`
- `created_at`
- `completed_at`
- `error_message`
- `limitations`

Notes:

- This is the top-level object the UI should render.
- The UI should group many `analyses` records under the same `asset_id`/ticker so repeated runs for AMD, SPY, or another symbol form a ticker research history.
- Analysis records remain immutable run lineage; ticker grouping is a read/navigation pattern, not a replacement for analysis-level records.
- `analysis_as_of` is the decision timestamp for model inputs and forecast targets. Live runs can use the current analysis time. Historical replay and training runs should use the article publish time or an explicit historical timestamp.

## `articles`

Stores article metadata and artifact references.

Fields:

- `id`
- `asset_id`
- `title`
- `source`
- `author`
- `url`
- `published_at`
- `retrieved_at`
- `input_type`: `manual_text` or `url`
- `raw_artifact_path`
- `extracted_text_artifact_path`
- `content_hash`
- `language`
- `word_count`
- `created_at`

Notes:

- `content_hash` supports duplicate detection.
- Large raw text should live in artifact storage.
- Articles are asset-scoped so the UI can show article/evidence history for a ticker across multiple analysis runs.

## `analysis_articles`

Join table linking analyses to articles.

Fields:

- `id`
- `analysis_id`
- `article_id`
- `relevance_score`
- `duplicate_group_id`
- `included_in_forecast`
- `exclusion_reason`

Notes:

- This table is the source of truth for which articles participated in which analysis runs.
- Ticker history views should use this relationship to show repeated article usage, duplicate handling, relevance decisions, and excluded evidence across runs for the same asset.

## `entities`

Stores normalized companies, tickers, products, sectors, themes, and keywords extracted from article evidence.

Fields:

- `id`
- `entity_type`: `asset`, `company`, `product`, `theme`, `sector`, `keyword`
- `name`
- `symbol`
- `canonical_name`
- `aliases`
- `created_at`
- `updated_at`

## `article_entities`

Links article evidence to extracted entities.

Fields:

- `id`
- `article_id`
- `entity_id`
- `provider`
- `model_name`
- `model_version`
- `confidence_score`
- `evidence_snippets`
- `created_at`

## `asset_relationships`

Stores known or inferred relationships between the primary ticker and related entities.

Fields:

- `id`
- `asset_id`
- `related_entity_id`
- `relationship_type`: `supplier`, `customer`, `partner`, `competitor`, `product_exposure`, `sector_peer`, `mentioned_with`
- `source`: `manual_seed`, `article_extraction`, `provider`
- `confidence_score`
- `created_at`
- `updated_at`

## `sentiment_runs`

Represents one sentiment-scoring run for one article.

Fields:

- `id`
- `analysis_id`
- `article_id`
- `provider`
- `model_name`
- `model_version`
- `sentiment_label`: `positive`, `neutral`, `negative`, `mixed`
- `sentiment_score`: numeric range should be standardized, e.g. `-1.0` to `1.0`
- `confidence_score`: `0.0` to `1.0`
- `drivers`: JSON list
- `evidence_snippets`: JSON list
- `limitations`: JSON list
- `raw_output_artifact_path`
- `created_at`

## `sentiment_aggregates`

Stores analysis-level sentiment summary.

Fields:

- `id`
- `analysis_id`
- `article_count`
- `included_article_count`
- `positive_count`
- `neutral_count`
- `negative_count`
- `mixed_count`
- `aggregate_score`
- `agreement_score`
- `evidence_strength_score`
- `summary`
- `created_at`

Notes:

- `agreement_score` captures whether multiple articles support similar sentiment.
- `evidence_strength_score` should penalize single-source overconfidence.

## `forecast_runs`

Stores one forecast for one analysis and one horizon.

Fields:

- `id`
- `analysis_id`
- `asset_id`
- `horizon`: `next_close`, `3_trading_days`, `7_trading_days`
- `provider`
- `model_name`
- `model_version`
- `predicted_direction`: `up`, `down`, `flat`, `uncertain`
- `predicted_percent_change`
- `confidence_score`
- `baseline_direction`
- `baseline_percent_change`
- `feature_snapshot`: JSON
- `top_factors`: JSON
- `limitations`: JSON
- `created_at`
- `target_start_price`
- `target_start_time`
- `target_end_time`
- `feature_window_start_time`
- `feature_window_end_time`

Notes:

- Store multiple horizons per analysis.
- MVP UI displays 3 trading days by default.
- Feature windows should end at or before the analysis `analysis_as_of` timestamp.
- Forecast target windows should start from the analysis `analysis_as_of` timestamp, not from article ingestion time.

## `forecast_outcomes`

Stores actual market result after forecast horizon completes.

Fields:

- `id`
- `forecast_run_id`
- `actual_end_price`
- `actual_percent_change`
- `actual_direction`
- `direction_correct`
- `absolute_error`
- `baseline_direction_correct`
- `baseline_absolute_error`
- `evaluated_at`

## `snapshots`

Stores user-saved research snapshots.

Fields:

- `id`
- `analysis_id`
- `asset_id`
- `title`
- `notes`
- `created_at`

## `model_versions`

Tracks deployed or used model versions.

Fields:

- `id`
- `model_type`: `sentiment`, `forecast`, `extraction`
- `name`
- `version`
- `provider`
- `artifact_path`
- `parameters`: JSON
- `created_at`
- `notes`

## `provider_calls`

Optional but useful for debugging provider failures and latency.

Fields:

- `id`
- `analysis_id`
- `provider`
- `operation`
- `status`
- `latency_ms`
- `error_message`
- `created_at`

## Relationships

```text
assets
  -> market_quotes
  -> market_price_history
  -> ticker_contexts
  -> asset_relationships
  -> analyses
      -> analysis_articles
          -> articles
              -> article_entities
                  -> entities
              -> sentiment_runs
      -> sentiment_aggregates
      -> forecast_runs
          -> forecast_outcomes
      -> snapshots
      -> provider_calls
```

## Artifact Storage Paths

Recommended local paths:

```text
data/
  raw/
    articles/
      {asset_symbol}/{article_id}.txt
      {asset_symbol}/{article_id}.html
  processed/
    articles/
      {asset_symbol}/{article_id}.json
  artifacts/
    sentiment/
      {sentiment_run_id}.json
    forecasts/
      {forecast_run_id}.json
    providers/
      {provider_call_id}.json
  reports/
    evaluations/
      {date}.json
```

## Initial MVP Schema Priority

Build first:

1. `assets`
2. `analyses`
3. `articles`
4. `analysis_articles`
5. `sentiment_runs`
6. `sentiment_aggregates`
7. `forecast_runs`
8. `forecast_outcomes`

Defer:

- `snapshots`, unless save/view snapshot is built in the first UI.
- `provider_calls`, unless debugging provider behavior becomes painful.
- `model_versions`, if model version can initially be stored directly on sentiment and forecast runs.

## Data Rules

- Every forecast must reference an analysis.
- Every forecast must include a model name and model version.
- Every forecast must include a horizon.
- Every forecast must be evaluable later.
- Every analysis must define the `analysis_as_of` timestamp used to align article evidence, market features, forecast targets, and outcomes.
- Historical analysis must not use market data, article evidence, or outcome data that became available after `analysis_as_of`.
- Sentiment evidence should never be detached from its source article.
- Raw article text should be persisted before model scoring.
- Missing market metrics should be stored as null, not fabricated.
