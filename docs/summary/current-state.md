# micromarket Current State

Last updated: 2026-04-26

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
- The first backend persistence slice is now implemented in the working tree:
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
  - API tests use a fake market-data provider so unit tests stay offline and deterministic.
- Baseline sentiment slice has started:
  - `app/sentiment/baseline.py` implements a deterministic lexicon-based sentiment provider.
  - `POST /analyses` scores each persisted manual article, writes `sentiment_runs`, creates one `sentiment_aggregate`, and returns sentiment metadata.
  - Tests cover positive, negative, and neutral baseline sentiment behavior.

## Decisions From Questionnaire

### Product Scope

- v1 market scope: US equities + ETFs.
- MVP interaction model: one ticker at a time.
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
   - rule-based baseline,
   - FinBERT/local transformer sentiment,
   - OpenAI/LLM sentiment extraction,
   - hybrid baseline plus LLM explanation.

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
8. Next: implement baseline forecast service and persisted forecast records.
9. Then broaden persisted create/read tests as forecast records land.

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

Reason: the project's highest-risk work is data/model quality, not API throughput. Python will reduce friction for ingestion, NLP, model evaluation, notebooks, and experimentation. Go can still be introduced later behind stable service boundaries if needed.

## Future Session Checklist

When resuming:

1. Read this file.
2. Read `07-product-decisions-questionnaire.md`.
3. Read `08-architecture-options.md`.
4. Read `09-technical-architecture.md`, `10-data-model.md`, `11-model-evaluation-plan.md`, and `12-implementation-roadmap.md`.
5. Inspect `apps/web`, `services/api`, `infra`, and `data`.
6. Run or install dependencies as needed:
   - `cd apps/web && npm install`
   - backend venv should already exist at `services/api/.venv`; if rebuilding: `cd services/api && python3 -m venv .venv && source .venv/bin/activate && python -m pip install -e ".[dev]"`
7. Verify backend tests with `cd services/api && source .venv/bin/activate && python -m pytest`.
8. Run lint with `cd services/api && source .venv/bin/activate && python -m ruff check app tests`.
9. Apply database migrations with `cd services/api && source .venv/bin/activate && alembic upgrade head`.
10. Optional notebook setup: `cd services/api && source .venv/bin/activate && python -m pip install -e ".[dev,notebooks]"`.
11. Continue with the backend vertical slice: baseline forecasts and persisted forecast records.
