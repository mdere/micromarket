# micromarket Ticker Context Ingestion Plan

## Goal

Create a stable ticker research context before improving sentiment or forecast models.

When a ticker such as `AMD` is first analyzed, the system should build enough local context to compare article sentiment against recent and future market movement without using future data.

## Core Idea

A ticker should have a reusable research context:

- primary ticker,
- configurable historical market lookback window,
- stored price history,
- related companies, products, partners, suppliers, customers, competitors, and sectors,
- article narratives and keywords,
- article-to-entity relationships,
- analysis as-of timestamps and forecast target windows.

This foundation lets the system ask:

- What was the market doing before this article?
- What happened after this article?
- Which related companies or themes appeared in the article?
- Do later supporting or contradicting articles mention the same entities?
- Does sentiment around a partner, supplier, or competitor appear to influence the primary ticker?

## Ticker Onboarding Flow

When a new ticker is introduced:

1. Normalize and persist the primary asset.
2. Fetch and store market history for a configurable lookback, such as 30 days.
3. Store the provider, retrieval time, and date range for the market history.
4. Prepare the ticker workspace for repeated analyses.
5. Reuse stored history when possible instead of refetching the same range.

The lookback should be configurable:

```text
MARKET_LOOKBACK_DAYS=30
```

Longer windows can be used later for better momentum, volatility, and baseline features.

## Historical Article Flow

When an article is analyzed:

1. Resolve `analysis_as_of` from article `published_at`, live time, or an explicit historical timestamp.
2. Ensure the primary ticker has market history ending at `analysis_as_of`.
3. Fetch missing historical prices before `analysis_as_of` if the local store has gaps.
4. Score article relevance to the primary ticker.
5. Extract related entities and narrative keywords.
6. Generate sentiment and forecast features using only data available at or before `analysis_as_of`.
7. Store forecast target windows after `analysis_as_of`.

Example:

```text
today: 2026-04-01
primary ticker: NVDA
article published_at: 2026-03-25
related entities: TSMC, Samsung, HBM, foundry capacity
market lookback: 30 days ending on 2026-03-25
forecast target: 2026-03-25 + next_close / 3 trading days / 7 trading days
```

## Entity Extraction

The first implementation should be deterministic and transparent before relying on LLM extraction.

Start with:

- ticker aliases,
- company names,
- known suppliers,
- known customers,
- known competitors,
- sector and product keywords,
- exact text matches and simple alias normalization.

Examples:

```text
TSMC
Taiwan Semiconductor
Taiwan Semiconductor Manufacturing Company
TSM
```

should normalize to the same related entity where possible.

Later providers can use local LLM extraction, but they should write to the same entity contract and preserve provider/model version lineage.

## Suggested Data Additions

### `market_price_history`

Stores historical daily or intraday market values used for lookbacks and outcomes.

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

### `ticker_contexts`

Stores local onboarding state for a ticker.

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

### `entities`

Stores normalized companies, tickers, products, themes, sectors, and keywords.

Fields:

- `id`
- `entity_type`: `asset`, `company`, `product`, `theme`, `sector`, `keyword`
- `name`
- `symbol`
- `canonical_name`
- `aliases`
- `created_at`
- `updated_at`

### `article_entities`

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

### `asset_relationships`

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

## First Implementation Slice

1. Add `market_price_history` and a history backfill service behind `MarketDataProvider`.
2. Add configurable lookback days with a default of 30.
3. Backfill missing ticker history when a ticker is first analyzed.
4. Store feature-window metadata on forecast runs.
5. Add tests with fake market data providers for complete, partial, and missing historical windows.

Implementation status:

- `market_price_history`, `ticker_contexts`, `analysis_as_of`, and forecast feature-window fields are implemented.
- Analysis creation now backfills market history and uses article `published_at` as the historical decision point when supplied.
- Related-entity extraction is still pending and should be the next slice.

## Second Implementation Slice

1. Add deterministic entity extraction.
2. Add `entities`, `article_entities`, and `asset_relationships`.
3. Add alias normalization for common ticker/company names.
4. Show related entities and narrative keywords in API responses.
5. Add tests for examples such as `NVDA` articles mentioning `TSMC` and `Samsung`.

## Guardrails

- Do not use future market data for historical features.
- Do not infer investment advice from entity relationships.
- Preserve provider/model lineage for extracted entities.
- Keep extraction deterministic at first.
- Use fake providers in tests.
- Treat related-company signals as research context until evaluated.
