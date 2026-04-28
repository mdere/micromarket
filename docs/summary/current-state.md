# micromarket Current State

Last updated: 2026-04-28

## Purpose

micromarket is a personal AI/ML stock research system. It ingests manually supplied or URL-based company articles, analyzes sentiment, combines that evidence with market data, and produces a confidence-oriented forecast to help with investment research.

The product is research-only decision support. It should not issue direct buy/sell/hold instructions in MVP.

## Source Docs

- Product journey: `micromarket/docs/00-product-journey.md`
- PRD: `micromarket/docs/01-prd.md`
- UX/user flow: `micromarket/docs/02-ux-user-flow.md`
- MVP concept: `micromarket/docs/03-mvp-concept.md`
- MVP development plan: `micromarket/docs/04-mvp-development-plan.md`
- Test plan: `micromarket/docs/05-test-plan.md`
- v0 visual prompt: `micromarket/docs/06-v0-visual-prompt.md`
- Completed questionnaire: `micromarket/docs/07-product-decisions-questionnaire.md`
- Architecture options: `micromarket/docs/08-architecture-options.md`
- Technical architecture: `micromarket/docs/09-technical-architecture.md`
- Data model: `micromarket/docs/10-data-model.md`
- Model evaluation plan: `micromarket/docs/11-model-evaluation-plan.md`
- Implementation roadmap: `micromarket/docs/12-implementation-roadmap.md`
- Model quality plan: `micromarket/docs/13-model-quality-plan.md`
- Ticker context ingestion plan: `micromarket/docs/14-ticker-context-ingestion-plan.md`

## Approval State

- Product-management docs are approved as the current planning baseline.
- Architecture recommendation is approved.
- Project scaffolding has started.
- Current scaffold includes Next.js web app shell, FastAPI API skeleton, Docker Compose, environment example, and local data directories.
- npm registry has been reset to the public npm registry for local installs.
- Frontend dependencies were installed locally, producing `apps/web/package-lock.json`.
- Backend dependencies were installed locally in `services/api/.venv`.
- Backend package now supports local Python 3.10+ while the Docker image still uses Python 3.12.
- FastAPI/TestClient dependency stack is pinned for local stability: FastAPI `0.115.6`, Starlette `0.41.x`, Uvicorn `0.30.x`, AnyIO `3.7.x`, and HTTPX `0.27.x`.
- `services/api/README.md` now contains comprehensive local setup, Docker Compose, verification, testing, and troubleshooting instructions.
- Current backend setup commit: `71d6acc` (`Set up backend local dependencies`).
- The first backend persistence slice is implemented:
  - SQLAlchemy MVP models exist under `services/api/app/db/models.py`.
  - Alembic is configured under `services/api/alembic`.
  - `POST /analyses` persists manual text analyses, assets, articles, analysis/article joins, and raw text artifacts.
  - `GET /analyses/{analysis_id}` and `GET /analyses` return persisted analysis/article metadata.
  - Focused API tests cover manual text create/read and empty evidence validation.
- Phase 1.5 notebook research workspace has been added:
  - `notebooks/README.md` documents setup, usage, and promotion rules.
  - Starter notebooks cover market data exploration, sentiment baseline inspection, forecast baseline calibration, and evaluation analysis.
  - `data/samples/sample_analysis_export.json` provides repeatable sample data before the database has enough real runs.
  - `services/api` now has an optional `notebooks` dependency group for Jupyter, ipykernel, pandas, and matplotlib.
- Market data provider slice has started:
  - `app/market_data/yfinance_provider.py` implements a `yfinance` quote provider behind the provider protocol.
  - `POST /analyses` fetches a quote through dependency injection, persists it in `market_quotes`, and returns quote metadata in the response.
  - `market_quotes.analysis_id` has been added through Alembic revision `20260426_0002` so quote snapshots are tied to the analysis that used them.
  - `market_quotes.volume` and `market_quotes.market_cap` use 64-bit integers after Alembic revision `20260427_0003` so live provider values do not overflow PostgreSQL `INTEGER`.
  - API tests use a fake market-data provider so unit tests stay offline and deterministic.
- Baseline sentiment slice has started:
  - `app/sentiment/baseline.py` implements a deterministic lexicon-based sentiment provider.
  - `POST /analyses` scores each persisted manual article, writes `sentiment_runs`, creates one `sentiment_aggregate`, and returns sentiment metadata.
  - Tests cover positive, negative, and neutral baseline sentiment behavior.
- Baseline forecast slice is implemented:
  - `app/forecasting/baseline.py` implements a deterministic rule-based forecast provider.
  - `POST /analyses` now creates forecast runs for `next_close`, `3_trading_days`, and `7_trading_days`.
  - Forecast records store provider/model versions, feature snapshots, top factors, limitations, no-change baseline fields, and target start/end metadata.
  - API responses now include stored forecast metadata.
  - Focused tests cover forecast generation and persisted analysis forecast responses.
- Evaluation refresh slice is implemented:
  - `POST /evaluations/refresh` finds expired forecast runs without outcomes and persists `forecast_outcomes`.
  - `GET /evaluations/summary` returns total evaluated forecasts plus per-horizon accuracy/error summaries.
  - The market-data provider interface now includes historical close lookup for evaluation.
  - Tests use a fake market-data provider so evaluation remains offline and deterministic.
- URL ingestion slice is implemented:
  - `app/ingestion/url_provider.py` defines a URL extraction provider protocol and `trafilatura` implementation.
  - `POST /analyses` accepts URL-only articles, stores raw HTML and extracted text artifacts, and runs the existing sentiment/forecast pipeline.
  - Manual text remains supported and takes precedence when both text and URL are supplied.
  - Tests use a fake URL extraction provider so URL ingestion stays offline and deterministic.
- Evidence filtering slice is implemented:
  - `app/ingestion/evidence.py` scores article relevance with deterministic ticker/market-context rules.
  - Duplicate content hashes and low-relevance articles are persisted but excluded from aggregate sentiment and forecast inputs.
  - Articles now need direct ticker evidence before they can be included in aggregate sentiment or forecast inputs; generic market context alone is not enough.
  - Article responses include relevance, duplicate group, inclusion, and exclusion metadata.
  - URL extraction failures return clear `502` responses and mark analyses as failed.
- Minimal UI slice is implemented:
  - `apps/web/app/page.tsx` now provides a usable analysis workflow over the API.
  - Users can submit a ticker with manual article text, a URL, or both.
  - The page renders primary forecast, sentiment aggregate, market quote, evidence metadata, limitations, and recent analyses.
  - UI language remains research-only and avoids buy/sell/hold advice.
- Product/UI decision added on 2026-04-28:
  - Analysis history should be grouped by ticker.
  - A ticker should behave like the durable workspace for repeated research runs.
  - Example: if AMD is analyzed 20 times with different articles, the user should be able to navigate to AMD and review all AMD analyses, submitted articles, evidence decisions, forecasts, sentiment, limitations, and later evaluation outcomes.
  - This is not a watchlist/multi-ticker batch feature; MVP remains one user-triggered ticker analysis at a time.
- Ticker-centered history slice is implemented:
  - `GET /analyses` accepts an optional `ticker` query parameter.
  - Analysis responses include `created_at` and `completed_at` timestamps for timeline display.
  - The web dashboard now loads a selected ticker workspace, renders a ticker-scoped analysis timeline, and shows selected-run evidence plus ticker-level article history.
  - Article titles link to source URLs when a URL is available.
  - Tests cover ticker-filtered analysis listing.
- UI error/evaluation visibility slice is implemented:
  - The dashboard shows persistent notices for API load failures, failed analyses, and evidence excluded from sentiment/forecast inputs.
  - The dashboard reads `GET /evaluations/summary` and renders a model-monitoring panel with horizon-level evaluated forecast counts, directional accuracy, model mean error, and baseline mean error.
  - The evaluation monitor can trigger `POST /evaluations/refresh`, show evaluated/skipped counts and provider errors, and reload the summary afterward.
- Next.js dashboard refactor is implemented:
  - `apps/web/app/page.tsx` now owns state and API orchestration.
  - Dashboard UI panels live under `apps/web/components/dashboard`.
  - Shared API response types and formatting helpers live under `apps/web/lib`.
- Panel-level loading and failed-analysis detail slice is implemented:
  - `AnalysisResponse` now exposes persisted `error_message` for failed analyses.
  - The dashboard shows loading states for ticker history, selected analysis fetches, and evaluation summary loads.
  - Failed analysis rows are visually distinct in the timeline, and failed-analysis notices include backend error details when available.
- Evidence grouping/filtering slice is implemented:
  - Selected run evidence now has filter controls for all, included, excluded, and duplicate articles with counts.
  - Evidence empty states are specific to the selected filter.
  - Ticker article history visually marks reused articles across multiple runs.
- Model-quality direction has been reevaluated:
  - `docs/13-model-quality-plan.md` is the next planning source for sentiment/model work.
  - Next major work should shift from UI mechanics to data/model foundation, model evaluation, and provider experimentation.
  - Recommended path is to build ticker context and as-of-time alignment first, then strengthen the deterministic sentiment baseline, then add an optional Ollama-backed sentiment provider behind the existing provider interface.
  - Google Colab and Databricks-style environments are acceptable for exploratory experiments only; production runtime should remain local-first.
- Historical time-alignment decision added:
  - Every analysis should resolve an `analysis_as_of` timestamp.
  - Live runs can use current analysis time; historical replay and training runs should use article `published_at` or an explicit historical timestamp.
  - Market feature lookbacks should end at `analysis_as_of`, forecast target windows should start at `analysis_as_of`, and outcomes should measure prices after the target horizon.
  - This is required before trusting sentiment/model-quality evaluation because it prevents lookahead bias.
- Ticker context ingestion decision added:
  - New tickers should trigger or reuse a configurable market-history backfill, such as 30 days.
  - Article ingestion should extract related companies, partners, suppliers, customers, competitors, products, themes, and keywords.
  - Related entities should preserve aliases and evidence snippets, for example normalizing `TSMC`, `Taiwan Semiconductor`, and `TSM`.
  - This foundation should be implemented before expanding sentiment fixtures or optional Ollama providers.
- Ticker market-history foundation slice is implemented:
  - `MARKET_LOOKBACK_DAYS` config defaults to 30.
  - `market_price_history` and `ticker_contexts` are modeled and covered by Alembic revision `20260428_0004`.
  - `MarketDataProvider` now supports daily price history, with `yfinance` and test fakes implementing the contract.
  - `POST /analyses` resolves `analysis_as_of`, backfills market history, stores feature-window timestamps, and uses historical close data for historical article forecasts.
  - API responses expose `analysis_as_of`, `analysis_as_of_source`, ticker context metadata, article `published_at`, and forecast feature-window timestamps.
  - Entity extraction is not implemented yet and remains the next foundation slice.

## Decisions From Questionnaire

### Product Scope

- v1 market scope: US equities + ETFs.
- MVP interaction model: one ticker at a time.
- Repeated analysis runs should be organized under the same ticker in the UI.
- Architecture should allow later watchlist/multi-ticker support without major refactor.
- Product is personal use first, not SaaS.
- Target runtime: home server first, possible AWS/S3/archive usage later.
- Initial users: AIML researcher and financial analyst workflows first.
- UI for family members and less technical users can come after data/API foundations are trustworthy.

### Prediction Goal

- Primary MVP forecast horizon is 3 trading days.
- Also store next-close and 7-trading-day forecasts for later evaluation.
- Priority outputs: percent movement and confidence score.
- Price range is not a priority for MVP.
- MVP quality should emphasize understandable sentiment summaries, better-than-naive baseline evaluation, and useful confidence flags.
- Bullish/bearish/neutral language is likely post-MVP, not v1.

### Data Sources

- v1 article ingestion order:
  1. Manually uploaded text.
  2. User-pasted URLs.
  3. APIs later.
- Free/open sources only for now.
- Paid APIs should be optional plugins that can be enabled temporarily.
- Recommended MVP market data provider is `yfinance` behind a replaceable provider interface.
- Real-time data is not needed for MVP.
- Manual refresh or delayed data is acceptable for research use.

### Model Strategy

- Start with a baseline model.
- Must include mechanisms for measuring improvement and retrospective evaluation.
- Home-server hosting is preferred.
- No strong local GPU available yet.
- OpenAI API or similar model API may be acceptable for sentiment/model assistance.
- Plain-English explanations are required and must link back to evidence.
- Forecasts must be stored for later accuracy evaluation.
- Model priority: accuracy first, explainability second.

### User Experience

- Dashboard should prioritize forecast first, then sentiment and article evidence.
- Dashboard navigation should make ticker history first-class: select or search a ticker, then review its analysis timeline and article evidence.
- Market metrics, risk warnings, and snapshots can be post-MVP or secondary.
- Avoid direct "buy", "sell", or "hold" commands in MVP.
- Need confidence-backed research output that helps judge whether to invest.
- Evidence should show summary plus amount/strength of supporting articles.
- Single high-sentiment article should not be over-trusted.
- Interface should be easy enough for family members eventually.

### Technical Preferences

- Frontend preference: server-side rendering framework, likely Next.js.
- Desired architecture: multiple backend services, potentially with Go services and a Next.js orchestrator/UI.
- Accepted backend architecture: FastAPI/Python owns ingestion, sentiment, forecasting, and evaluation APIs.
- User leans Go but recognizes Python is better for data/model work.
- PostgreSQL is acceptable for backend/general data.
- Model artifacts should live locally on the home server, with S3 or equivalent archive later.
- Local-only first.
- Avoid unmaintained frameworks.
- Avoid paid cloud services for now.

### MVP Constraints

- Timeline: 2-3 months.
- Built solo for now.
- Priority order: accuracy, explainability, polish, extensibility, low cost.

### Compliance and Risk

- Strictly research-only for MVP.
- User-specific financial context should be excluded from MVP.
- Every forecast should log or display model limitations.

## Key Product Interpretation

The next phase should focus less on UI polish and more on a trustworthy data/model backbone:

- ingest article text and URLs,
- normalize article records,
- score relevance and sentiment,
- generate forecast/confidence output,
- store all runs for evaluation,
- expose clear APIs,
- then layer the UI on top.

The architecture should avoid overbuilding SaaS features but should not box the project into a throwaway script. A modular local-first system is the right direction.

## Open Decisions

1. Market data provider:
   - recommended MVP default is `yfinance`,
   - keep provider interface open for Alpha Vantage, Finnhub, Polygon, or another provider later.

2. Sentiment provider:
   - current provider is a rule-based baseline,
   - next provider target is an optional Ollama/local LLM sentiment provider,
   - FinBERT/local transformer and hosted notebook experiments remain research options,
   - OpenAI or other APIs remain optional later providers, not default MVP runtime.

3. URL extraction library:
   - choose maintained Python package during implementation.

4. Scaffolding tooling:
   - choose package managers and migration tooling during project setup.

## Next Recommended Work

The architecture recommendation has been accepted:

- Next.js SSR UI.
- FastAPI/Python data and ML API.
- PostgreSQL structured storage.
- Local filesystem artifact storage.
- Optional S3-compatible archive later.
- Go deferred until a specific service boundary needs it.

The current work is implementing the first backend vertical slice:

1. SQLAlchemy models and Alembic migrations for the MVP tables are in place.
2. Manual article text ingestion now stores normalized text artifacts.
3. Analysis and article records are persisted through the API.
4. Jupyter notebook research workspace is in place for model/data exploration.
5. Market data provider implementation with `yfinance` is in place.
6. Market quote records are persisted and wired into `POST /analyses`.
7. Baseline sentiment provider and persistence are in place.
8. Baseline forecast provider and persisted forecast records are in place.
9. Evaluation refresh for expired forecasts and stored outcomes is in place.
10. URL ingestion over the stable analysis/evaluation backbone is in place.
11. Article relevance, duplicate handling, and extraction failure reporting are in place.
12. Minimal UI over the stable API response is in place.
13. Ticker-centered analysis history is implemented.
14. UI error states, evaluation summary visibility, and evaluation refresh controls are implemented.
15. Next.js dashboard component refactor is implemented.
16. Panel-level loading states and clearer failed-analysis detail are implemented.
17. Evidence grouping/filtering and article-history reuse markers are implemented.
18. Model-quality plan is documented.
19. Historical as-of-time alignment is documented as the next architecture correction.
20. Ticker context ingestion plan is documented.
21. Ticker onboarding, market-history backfill, and as-of-time aligned historical replay are implemented.
22. Next: implement related-entity and narrative keyword extraction before expanding sentiment provider complexity.

## Suggested Recommendation To Explore Next

The current recommended architecture is:

- Next.js for SSR UI and light orchestration.
- FastAPI/Python for ingestion, sentiment, forecasting, and model evaluation.
- Jupyter notebooks should be added as an MVP research workspace for data science exploration, baseline tuning, and evaluation analysis. They are not part of the production runtime.
- PostgreSQL for structured records.
- Local filesystem for raw article/model artifacts.
- S3-compatible archive later.
- Optional Go services later only where performance or long-running API stability clearly justify them.
- Primary forecast horizon: 3 trading days.
- Also store next-close and 7-trading-day forecasts for later evaluation.
- Start market data with `yfinance` behind a provider interface.
- Ticker-centered history is now the active UI shape: one ticker workspace lists analyses and articles for that ticker before watchlists or batch workflows are introduced.
- Continue model-quality foundation work by adding related-entity extraction next. Market-history backfill, `analysis_as_of`, historical market lookbacks, and forecast target windows are now started in code.
- After entity extraction is in place, improve deterministic sentiment fixtures and confidence/driver extraction, then add an optional Ollama sentiment provider behind `SentimentProvider`.

Reason: the project's highest-risk work is data/model quality, not API throughput. Python will reduce friction for ingestion, NLP, model evaluation, notebooks, and experimentation. Go can still be introduced later behind stable service boundaries if needed.

## Future Session Checklist

When resuming:

1. Read this file.
2. Read `docs/summary/operating-guide.md` for the north star, guardrails, commit discipline, and session-start protocol.
3. Check and compare recent commits with the summary:
   - `git status --short`
   - `git log --oneline -n 8`
   - `git show --stat --summary HEAD`
4. Read `07-product-decisions-questionnaire.md`.
5. Read `08-architecture-options.md`.
6. Read `09-technical-architecture.md`, `10-data-model.md`, `11-model-evaluation-plan.md`, and `12-implementation-roadmap.md`.
7. Inspect `apps/web`, `services/api`, `infra`, and `data`.
8. Run or install dependencies as needed:
   - `cd apps/web && npm install`
   - backend venv should already exist at `services/api/.venv`; if rebuilding: `cd services/api && python3 -m venv .venv && source .venv/bin/activate && python -m pip install -e ".[dev]"`
9. Verify backend tests with `cd services/api && source .venv/bin/activate && python -m pytest`.
10. Run lint with `cd services/api && source .venv/bin/activate && python -m ruff check app tests`.
11. Apply database migrations with `cd services/api && source .venv/bin/activate && alembic upgrade head`.
12. Optional notebook setup: `cd services/api && source .venv/bin/activate && python -m pip install -e ".[dev,notebooks]"`.
13. Read `docs/13-model-quality-plan.md`.
14. Read `docs/14-ticker-context-ingestion-plan.md`.
15. Implement related-entity and narrative keyword extraction.
16. Add curated sentiment fixtures and improve the deterministic baseline provider.
17. Keep Ollama, Colab, and Databricks work behind provider/research boundaries.
18. Keep the UI and model outputs research-only and avoid buy/sell/hold language.
