# micromarket Implementation Roadmap

## MVP Goal

Build a local-first end-to-end system that accepts a ticker and article evidence, scores sentiment, generates a confidence-oriented 3-trading-day forecast, stores all run lineage, and supports later forecast evaluation.

The MVP should keep analysis execution one ticker at a time while organizing history by ticker. A ticker acts as the durable research workspace for repeated runs, articles, evidence decisions, forecasts, sentiment, limitations, and later evaluation outcomes.

Historical model quality depends on ticker context and time alignment. Analyses should resolve an `analysis_as_of` timestamp, and all article evidence, market features, forecast targets, and outcomes should be computed relative to that timestamp to avoid lookahead bias. New tickers should also have local market-history context and related-entity extraction before model quality is judged.

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
  - market price history,
  - ticker contexts,
  - entities and article entities,
  - sentiment runs,
  - forecast runs,
  - forecast outcomes.

Acceptance criteria:

- API can create and retrieve a test analysis.
- Database schema supports the MVP data model.
- Analysis records can store the decision timestamp used for live or historical replay runs.
- Tests cover basic create/read paths.

## Phase 1.5: Research Notebook Workspace

Deliverables:

- Add a `notebooks/` workspace for exploratory data science.
- Add notebook setup instructions and optional research dependencies.
- Create starter notebooks for:
  - market data exploration,
  - sentiment baseline inspection,
  - forecast baseline calibration,
  - evaluation analysis.
- Establish the promotion rule: notebooks are for exploration; stable logic moves into tested backend modules.

Acceptance criteria:

- A notebook can read local API/database outputs or exported sample data.
- Notebook-generated reports can be saved under `data/reports`.
- No production API behavior depends on manually running a notebook.
- Secrets and local notebook checkpoints are ignored by Git.

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
- Article-related entities and narrative keywords can be extracted and persisted through a stable contract.

## Phase 3: Market Data Provider

Deliverables:

- `MarketDataProvider` interface.
- `yfinance` implementation.
- Quote/history retrieval.
- Historical lookback retrieval ending at an analysis as-of timestamp.
- Market history backfill for new ticker contexts.
- Asset lookup for US equities and ETFs.
- Market quote persistence.

Acceptance criteria:

- API retrieves quote and recent history for a common stock.
- API retrieves data for a common ETF.
- API can retrieve historical lookback data for a ticker without using prices after the requested as-of timestamp.
- API can backfill a configurable market-history window, such as 30 days, when a ticker is first analyzed.
- Provider errors return clear failure messages.
- Provider-specific objects do not leak across the app.

## Phase 3.5: Ticker Context And Entity Graph

Deliverables:

- Ticker context onboarding service.
- Configurable market-history lookback days.
- `market_price_history` persistence.
- Deterministic related-entity extraction.
- Alias normalization for companies and tickers.
- Article-to-entity relationship persistence.
- Asset-to-related-entity relationship persistence.

Acceptance criteria:

- Adding a ticker such as `AMD` stores or refreshes recent market history.
- An `NVDA` article mentioning `TSMC` or `Samsung` can persist those related entities.
- Entity extraction preserves provider/model version lineage.
- Tests use fake providers and deterministic extraction fixtures.

## Phase 4: Sentiment Pipeline

Deliverables:

- `SentimentProvider` interface.
- Baseline sentiment provider.
- Curated sentiment fixture set for repeatable provider evaluation.
- Improved deterministic baseline sentiment provider.
- Optional Ollama/local LLM-assisted sentiment provider if configured.
- Evidence snippets and driver extraction.
- Sentiment aggregate generation.

Acceptance criteria:

- Every article receives sentiment label, score, confidence, and evidence.
- Analysis receives aggregate sentiment and evidence-strength score.
- Low article count and conflicting evidence reduce confidence.
- Sentiment run records include model name/version.
- Provider tests remain deterministic and offline through fake providers.
- Ollama or hosted notebook experiments are optional and do not become production runtime requirements.

## Phase 5: Forecast Pipeline

Deliverables:

- Rule-based baseline forecast model.
- As-of-time aligned feature snapshot generation.
- Forecast records for:
  - next close,
  - 3 trading days,
  - 7 trading days.
- Primary forecast output for 3 trading days.
- Forecast limitations and top factors.

Acceptance criteria:

- Analysis produces forecasts for all MVP horizons.
- Forecast records include model version and feature snapshot.
- Forecast records include feature-window and target-window timestamps.
- Historical forecasts start from the analysis as-of timestamp, not ingestion time.
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
- Outcome lookup starts from the stored forecast target window.
- Directional correctness and absolute error are calculated.
- Model performance can be compared to no-change and momentum baselines.

## Phase 7: Web Dashboard

Deliverables:

- Ticker input.
- Ticker-centered history view.
- Manual article text form.
- URL input form.
- Analysis result page.
- Forecast card.
- Sentiment summary.
- Evidence article list.
- Limitations panel.
- Analysis timeline scoped to the selected ticker.
- Article/evidence history scoped to the selected ticker.

Acceptance criteria:

- User can run a complete analysis from the browser.
- User can select a ticker such as AMD and see all analysis runs previously created for AMD.
- User can inspect which articles were analyzed for that ticker and which analysis runs used each article.
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
3. Research notebook workspace.
4. Manual text ingestion.
5. Market data provider.
6. Baseline sentiment.
7. Baseline forecast.
8. Evaluation storage.
9. Minimal Next.js UI.
10. URL ingestion.
11. Evaluation refresh.
12. Ticker-centered analysis history.
13. Ticker context onboarding and market-history backfill.
14. Related-entity and narrative keyword extraction.
15. Analysis as-of time and historical market lookback alignment.
16. Sentiment fixture set and improved baseline sentiment.
17. Optional Ollama sentiment provider.

## Risks

### Model Signal Is Weak

Mitigation:

- Store all runs.
- Build ticker market-history context before evaluating article impact.
- Extract related entities and narrative keywords so sentiment can be grouped by theme, partner, supplier, customer, or competitor.
- Compare to baselines.
- Treat early forecasts as experiments.
- Use notebooks to inspect failures, tune baseline parameters, and validate confidence calibration before promoting changes into API code.
- Improve sentiment quality before adding forecast complexity.
- Compare baseline, local LLM, and any hosted experiments against the same fixture set.

### Historical Evaluation Uses Future Data

Mitigation:

- Store `analysis_as_of` for every analysis.
- Store feature-window start/end and forecast target-window start/end for every forecast.
- Derive historical runs from article `published_at` or an explicit historical timestamp.
- Fetch market lookback windows ending at `analysis_as_of`.
- Reject or flag articles whose publish time is after the analysis as-of time.

### Related Entity Signal Is Noisy

Mitigation:

- Start deterministic with alias dictionaries and exact matches.
- Store confidence and evidence snippets for every extracted entity.
- Treat relationships as research context until evaluated.
- Normalize common aliases such as `TSMC`, `Taiwan Semiconductor`, and `TSM`.

### LLM Output Is Unstable

Mitigation:

- Require structured JSON output.
- Validate model responses before persistence.
- Store provider/model versions and limitations.
- Keep deterministic baseline fallback available.
- Use fake providers in tests instead of requiring Ollama or hosted services.

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
- User can revisit prior analyses grouped by ticker.
- New ticker onboarding stores recent market history for repeatable context.
- Articles can preserve related company, product, partner, supplier, customer, competitor, and keyword relationships.
- System produces sentiment, forecast, confidence, and limitations.
- Sentiment provider quality is measured against curated fixtures.
- Forecast records are stored with model version and horizon.
- Forecast and evaluation records are aligned to analysis as-of time.
- Evaluation refresh can compare expired forecasts to actual outcomes.
- UI presents forecast and evidence without direct financial advice language.
