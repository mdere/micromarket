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
- Deterministic related-entity extraction is implemented for the first alias/theme set.

## Second Implementation Slice

1. Add deterministic entity extraction.
2. Add `entities`, `article_entities`, and `asset_relationships`.
3. Add alias normalization for common ticker/company names.
4. Show related entities and narrative keywords in API responses.
5. Add tests for examples such as `NVDA` articles mentioning `TSMC` and `Samsung`.

Implementation status:

- `entities`, `article_entities`, and `asset_relationships` are implemented.
- `POST /analyses` extracts related entities from article text, persists article/entity links, and returns entity metadata in article responses.
- The first deterministic dictionary covers examples such as `TSMC`, `Samsung`, `HBM`, `AI chips`, and `foundry capacity`.
- Next model-quality slice should add curated sentiment fixtures and improve baseline sentiment scoring.

## Tracking Needs And Related Asset Roadmap

The next product direction is to turn extracted entities into explicit research leads.

When an analysis for a primary ticker mentions related companies, assets, products, customers, suppliers, competitors, or themes, the ticker workspace should show those associations and explain why they may matter. A user should be able to click a related asset such as `TSM`, `MSFT`, `AMZN`, or `NVDA`, open that asset's own ticker workspace, feed in articles, and later compare related-asset sentiment and market movement against the primary ticker.

This should remain research-only. Related assets should be treated as context and follow-up candidates, not as buy/sell/hold recommendations.

### Current Foundation

Already implemented:

- `entities` stores normalized related assets, companies, products, themes, and keywords.
- `article_entities` links article evidence to extracted entities with provider/model lineage and evidence snippets.
- `asset_relationships` links the primary ticker's asset to related entities with relationship types such as `supplier`, `customer`, `competitor`, `product_exposure`, and `mentioned_with`.
- Article responses include extracted entities, relationship type, confidence, evidence snippets, and extraction lineage.
- Ticker workspaces already group repeated analyses and article history by primary ticker.

Not yet implemented:

- A first-class per-analysis "tracking needs" object.
- A backend response surface that aggregates related entities into prioritized ticker-workspace suggestions.
- A UI panel for related assets, companies, and themes.
- One-click navigation from a related ticker/entity into its own ticker workspace.
- Automatic market-history onboarding for related tickers suggested by an analysis.
- Correlation or proportional-impact analysis between a primary ticker and related assets.

### Proposed Data Addition: `analysis_tracking_needs`

Add a table that records follow-up tracking suggestions generated from each analysis.

Fields:

- `id`
- `analysis_id`
- `primary_asset_id`
- `entity_id`
- `suggested_symbol`
- `tracking_type`: `related_ticker`, `supplier`, `customer`, `competitor`, `product_theme`, `macro_theme`, `unknown`
- `reason`
- `evidence_snippets`
- `priority_score`
- `status`: `suggested`, `accepted`, `ignored`, `tracked`
- `provider`
- `model_name`
- `model_version`
- `created_at`
- `updated_at`

Initial tracking needs can be generated deterministically from `article_entities` and `asset_relationships`:

- related entities with a symbol become `related_ticker` candidates,
- suppliers/customers/competitors get higher priority than generic mentions,
- products/themes are suggested as context but do not need market-history onboarding,
- repeated mentions across articles or analyses increase priority,
- low-confidence or generic `mentioned_with` entities remain lower priority.

### Backend Slice

1. Add `AnalysisTrackingNeed` model and Alembic migration.
2. Add a deterministic tracking-needs generator behind a small service interface.
3. Generate tracking needs after article entities are persisted.
4. Add tracking needs to `AnalysisResponse`.
5. Add focused tests:
   - an `NVDA` article mentioning `TSMC`, `Samsung`, and `HBM` returns tracking needs,
   - ticker-backed entities include `suggested_symbol`,
   - product/theme entities do not trigger market-history onboarding yet,
   - repeated entities update or preserve priority without duplicates.

### Web App Slice

1. Extend frontend API types to include article entities and tracking needs.
2. Add a ticker-workspace panel such as `Related Signals` or `Tracking Needs`.
3. Show:
   - related ticker/company/theme,
   - relationship type,
   - priority/confidence,
   - evidence snippet,
   - status.
4. Make related ticker symbols clickable so selecting `TSM` or `MSFT` loads that ticker workspace.
5. Keep product/theme rows visible as context even when they are not clickable tickers.
6. Do not show investment advice language.

### Later Correlation Slice

Only after related assets have their own article/sentiment/history data:

1. Ensure related assets have market history over aligned windows.
2. Compare primary ticker sentiment and price movement with related-asset sentiment and price movement using `analysis_as_of` aligned windows.
3. Start with descriptive metrics:
   - co-mention count,
   - related-asset sentiment direction,
   - related-asset price move over matching horizons,
   - primary ticker price move over matching horizons.
4. Add correlation-style metrics only once enough historical observations exist.
5. Treat correlations as exploratory research context, not forecasts or investment advice.

## Next Recommended Slice

Implement `analysis_tracking_needs` and surface it in the API before expanding the web UI.

Reason: the backend already captures raw related entities and relationships, but the user-facing workflow needs a stable, prioritized object that says "track this because this article connected it to the primary ticker." Once that object exists, the web app can render it cleanly and later use it for related-ticker navigation.

## Guardrails

- Do not use future market data for historical features.
- Do not infer investment advice from entity relationships.
- Preserve provider/model lineage for extracted entities.
- Keep extraction deterministic at first.
- Use fake providers in tests.
- Treat related-company signals as research context until evaluated.
- Keep tracking needs as suggestions until the user accepts or enough evidence supports promotion.
