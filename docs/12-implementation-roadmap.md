# micromarket Implementation Roadmap

## MVP Goal

Build a local-first end-to-end system that accepts a ticker and article evidence, scores sentiment, generates a confidence-oriented 3-trading-day forecast, stores all run lineage, and supports later forecast evaluation.

## Phase 0: Project Setup

Deliverables:

- Create repo structure:
  - `apps/web`
  - `services/api`
  - `infra`
  - `data`
- Add Docker Compose for PostgreSQL.
- Add environment variable examples.
- Add basic README run instructions.

Acceptance criteria:

- PostgreSQL starts locally.
- FastAPI health endpoint works.
- Next.js app starts locally.

## Phase 1: Backend Foundation

Deliverables:

- FastAPI app skeleton.
- Configuration management.
- Database connection.
- Initial migrations.
- Core models:
  - assets,
  - analyses,
  - articles,
  - sentiment runs,
  - forecast runs,
  - forecast outcomes.

Acceptance criteria:

- API can create and retrieve a test analysis.
- Database schema supports the MVP data model.
- Tests cover basic create/read paths.

## Phase 2: Article Ingestion

Deliverables:

- Manual article text endpoint.
- URL ingestion endpoint.
- Article normalization.
- Local artifact write/read.
- Duplicate hash generation.

Acceptance criteria:

- User can submit article text for a ticker.
- User can submit a URL and store extracted text.
- Raw/extracted artifacts are saved locally.
- Article metadata is persisted in PostgreSQL.

## Phase 3: Market Data Provider

Deliverables:

- `MarketDataProvider` interface.
- `yfinance` implementation.
- Quote/history retrieval.
- Asset lookup for US equities and ETFs.
- Market quote persistence.

Acceptance criteria:

- API retrieves quote and recent history for a common stock.
- API retrieves data for a common ETF.
- Provider errors return clear failure messages.
- Provider-specific objects do not leak across the app.

## Phase 4: Sentiment Pipeline

Deliverables:

- `SentimentProvider` interface.
- Baseline sentiment provider.
- Optional LLM-assisted sentiment provider if API key exists.
- Evidence snippets and driver extraction.
- Sentiment aggregate generation.

Acceptance criteria:

- Every article receives sentiment label, score, confidence, and evidence.
- Analysis receives aggregate sentiment and evidence-strength score.
- Low article count and conflicting evidence reduce confidence.
- Sentiment run records include model name/version.

## Phase 5: Forecast Pipeline

Deliverables:

- Rule-based baseline forecast model.
- Forecast records for:
  - next close,
  - 3 trading days,
  - 7 trading days.
- Primary forecast output for 3 trading days.
- Forecast limitations and top factors.

Acceptance criteria:

- Analysis produces forecasts for all MVP horizons.
- Forecast records include model version and feature snapshot.
- Forecast can return `uncertain`.
- Forecast explanation links back to article/sentiment evidence.

## Phase 6: Evaluation Loop

Deliverables:

- Outcome refresh endpoint.
- Baseline comparisons.
- Evaluation summary endpoint.
- Basic evaluation report.

Acceptance criteria:

- Expired forecasts can be evaluated.
- Actual outcome is stored.
- Directional correctness and absolute error are calculated.
- Model performance can be compared to no-change and momentum baselines.

## Phase 7: Web Dashboard

Deliverables:

- Ticker input.
- Manual article text form.
- URL input form.
- Analysis result page.
- Forecast card.
- Sentiment summary.
- Evidence article list.
- Limitations panel.
- Basic recent analyses list.

Acceptance criteria:

- User can run a complete analysis from the browser.
- UI displays forecast, confidence, sentiment, and evidence.
- UI avoids direct buy/sell/hold instructions.
- Limitations appear with every forecast.

## Phase 8: Local Deployment Polish

Deliverables:

- Docker Compose for web, API, and database.
- Local artifact directory mapping.
- Seed/demo script.
- Basic logs.
- Documentation update.

Acceptance criteria:

- Full app runs locally from documented commands.
- Demo analysis can be run from clean setup.
- Logs show pipeline stages without leaking secrets.

## First Vertical Slice

Build this before broadening scope:

1. Submit ticker `SPY` or `AAPL`.
2. Paste one article manually.
3. Store article and artifact.
4. Score sentiment.
5. Fetch market quote.
6. Generate 3-trading-day forecast.
7. Store forecast.
8. Display result in API response.

Only after this works should the UI and URL ingestion expand.

## Suggested Build Order

1. Backend health/database.
2. Data model and migrations.
3. Manual text ingestion.
4. Market data provider.
5. Baseline sentiment.
6. Baseline forecast.
7. Evaluation storage.
8. Minimal Next.js UI.
9. URL ingestion.
10. Evaluation refresh.

## Risks

### Model Signal Is Weak

Mitigation:

- Store all runs.
- Compare to baselines.
- Treat early forecasts as experiments.

### Article Extraction Is Unreliable

Mitigation:

- Manual text remains supported.
- Store raw artifacts.
- Label extraction failures clearly.

### Scope Creep Into Microservices

Mitigation:

- Keep Go out of MVP.
- Keep synchronous analysis until latency or reliability requires jobs.
- Build stable provider interfaces instead of extra services.

### UI Distracts From Pipeline Quality

Mitigation:

- Build API-first vertical slice.
- Add UI after analysis result shape is stable.

## Definition of MVP Done

MVP is done when:

- Local app runs end-to-end.
- User can analyze one ticker with manual text and pasted URL evidence.
- System produces sentiment, forecast, confidence, and limitations.
- Forecast records are stored with model version and horizon.
- Evaluation refresh can compare expired forecasts to actual outcomes.
- UI presents forecast and evidence without direct financial advice language.
