# micromarket Product Journey

## Toolkit Mapping

This package applies the AI Product Development Toolkit sequence to micromarket:

1. PRD: Define the broader product requirements and constraints.
2. UX/User Flow: Convert requirements into screens, flows, states, and interface behavior.
3. MVP Concept: Narrow the first testable slice.
4. MVP Development Plan: Define build scope, stack, phases, risks, and launch criteria.
5. Testing Plan: Define what must be verified before pilot use.
6. v0 Prompt: Prepare a frontend-generation prompt for the MVP interface.

## Product Vision

micromarket helps individual investors and research-oriented traders understand how recent company news, article sentiment, and market context may relate to short-term price movement. It combines article ingestion, sentiment modeling, price prediction, and stock-market metrics in one explainable research workspace.

The product must be evidence-first. Users should see the articles, sentiment drivers, prediction confidence, historical context, and market metrics behind any generated outlook.

## User Journey

1. User enters or selects a ticker.
2. System retrieves company profile, latest price data, and recent article sources.
3. User reviews article ingestion status and source quality.
4. System computes sentiment, entity relevance, article impact score, and trend direction.
5. System combines sentiment features with market features to produce a forecast range.
6. User sees a dashboard with signal summary, forecast, confidence, evidence, and risk notes.
7. User can drill into specific articles, sentiment drivers, and model explanations.
8. User saves a watchlist item or research snapshot.
9. User compares the latest snapshot against prior snapshots over time.

## Key Product Principles

- Transparency over magic: every signal must be traceable to data.
- Decision support over advice: no personalized financial recommendations.
- Confidence-aware predictions: show ranges and uncertainty, not false precision.
- Source quality matters: label article source, recency, duplicate coverage, and relevance.
- Human control: user decides whether to buy, sell, hold, or ignore.

## End-to-End Product Roadmap

### Phase 0: Discovery and Foundations

- Confirm target user segment and preferred market coverage.
- Pick initial article sources and stock data providers.
- Define model-evaluation metrics and baseline prediction approach.
- Define legal/compliance language for investment-risk disclaimers.

### Phase 1: MVP

- Single ticker dashboard.
- Article ingestion from configured sources.
- Sentiment analysis and source list.
- Basic market metrics.
- Price-movement prediction range with confidence.
- Evidence panel explaining key sentiment drivers.
- Manual refresh and saved research snapshot.

### Phase 2: Portfolio Research Workspace

- Watchlist with multiple tickers.
- Alerts for sentiment shifts and major article clusters.
- Historical snapshot timeline.
- Model performance tracking by ticker and sector.
- Comparison between companies.

### Phase 3: Advanced Modeling

- Sector-adjusted sentiment weighting.
- Earnings-event and macro-event awareness.
- Backtesting workflow.
- Multiple model strategies with benchmark comparison.
- Personalized research preferences without personalized financial advice.

### Phase 4: Collaboration and Production Hardening

- User accounts.
- Shared research notes.
- Data lineage and audit logs.
- Paid data-source integrations.
- Stronger compliance review and production monitoring.

## Primary Open Questions

- Which markets are in scope first: US equities only, or broader?
- Which article sources will be used first: free web/RSS, NewsAPI, SEC filings, paid providers, or user-submitted URLs?
- What prediction horizon matters most: intraday, next close, 3-day, 7-day, or 30-day?
- Should the first model optimize for directional accuracy, percent change error, or risk-adjusted signal quality?
- Will this be a personal research tool first or a multi-user SaaS product?
