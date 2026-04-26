# micromarket Architecture Options

## Context

micromarket is a personal, local-first AI/ML stock research system. The MVP should support US equities + ETFs, one ticker at a time, manually uploaded article text, pasted article URLs, baseline sentiment/forecast modeling, stored forecasts, and retrospective model evaluation.

The main architectural pressure is not high traffic. The main pressure is building a trustworthy data and model pipeline that can evolve without forcing major rewrites.

## Decision Criteria

Architecture should optimize for:

- Accuracy and model-evaluation workflow.
- Explainability and evidence traceability.
- Solo-developer implementation over 2-3 months.
- Local/home-server deployment.
- PostgreSQL for structured data.
- Local filesystem for raw artifacts and model files.
- Optional S3-compatible archive later.
- Future extension to watchlists and multiple tickers.
- Minimal paid cloud dependency.
- Avoiding unmaintained frameworks.

## Option 1: Python-Only Modular Monolith

### Shape

```text
Browser
  -> Python web app/API
      -> ingestion module
      -> article parser module
      -> sentiment module
      -> forecast module
      -> evaluation module
      -> PostgreSQL
      -> local artifact storage
```

Possible frameworks:

- FastAPI with server-rendered templates or a simple frontend.
- Streamlit/Dash for a research-first interface.
- Django if admin/data-management workflows matter early.

### Pros

- Fastest path to data and model work.
- Lowest language and service complexity.
- Excellent Python ecosystem for NLP, ML, evaluation, notebooks, pandas, scikit-learn, transformers, and financial-data experimentation.
- Easy to run locally on a home server.
- Easy to debug end-to-end.
- Good fit for researcher-first MVP.

### Cons

- UI may feel less polished unless extra frontend work is added.
- If using Streamlit/Dash, later migration to a family-friendly product UI may require rework.
- If API boundaries are not designed intentionally, modules can become tangled.
- Less aligned with your preference for SSR frontend orchestration.

### Best Fit

Best if the first goal is proving the data/model pipeline before committing to a richer UI.

### Risk

The project may become a research app rather than a product-ready application if frontend architecture is deferred too long.

## Option 2: Next.js + FastAPI

### Shape

```text
Browser
  -> Next.js SSR UI
      -> FastAPI service
          -> ingestion
          -> URL extraction
          -> sentiment pipeline
          -> forecast pipeline
          -> evaluation jobs
          -> PostgreSQL
          -> local artifact storage
```

### Pros

- Strong balance between product UI and ML workflow.
- Next.js gives a clean SSR frontend for family-friendly UX later.
- FastAPI keeps Python close to the ML/data pipeline.
- Clear separation between UI/orchestration and model/data services.
- Easy to add API endpoints for future Go services if needed.
- Good local deployment path using Docker Compose.
- PostgreSQL and filesystem storage fit naturally.
- Avoids premature microservice complexity.

### Cons

- Two runtimes from day one: Node.js and Python.
- Requires API contract discipline.
- Slightly slower initial setup than Python-only.
- Some orchestration decisions must be made early: whether Next.js calls FastAPI directly or wraps backend calls through server actions/API routes.

### Best Fit

Best if the MVP should prove the model pipeline while also building toward a real web product.

### Risk

The UI can distract from model/evaluation quality if scope is not controlled.

## Option 3: Next.js + Go API Gateway + Python ML Service

### Shape

```text
Browser
  -> Next.js SSR UI
      -> Go API gateway
          -> Python ML/data service
          -> PostgreSQL
          -> local artifact storage
```

### Pros

- Matches your interest in Go for service/API layers.
- Go is excellent for stable APIs, concurrency, low memory usage, and long-running backend services.
- Python remains available for ML, sentiment, evaluation, and data processing.
- Creates strong service boundaries early.
- Can scale cleanly if the product eventually grows beyond personal use.

### Cons

- More complexity than the MVP needs.
- Three main runtimes from day one: Node.js, Go, Python.
- More API contracts, deployment units, logging surfaces, and failure modes.
- Slower solo-developer velocity.
- Go layer may mostly pass requests through until real performance or orchestration needs emerge.

### Best Fit

Best if the project goal is to practice or prove a microservice architecture alongside the product.

### Risk

Architecture work may outrun product learning. The highest-risk area is model/data quality, and this option spends early time on service structure.

## Option 4: Next.js Full-Stack + Python Worker

### Shape

```text
Browser
  -> Next.js app
      -> Next.js server routes/actions
          -> PostgreSQL
          -> job queue / subprocess / worker trigger
              -> Python worker
                  -> ingestion
                  -> sentiment
                  -> forecast
                  -> evaluation
          -> local artifact storage
```

### Pros

- Next.js owns UI and app orchestration.
- Python is used where it is strongest: ML/data jobs.
- Clear product-facing app surface.
- Can start simple with synchronous worker calls, then evolve to a queue.
- Good fit for local-first deployment if packaged with Docker Compose.

### Cons

- Next.js backend can become an awkward middle layer for data/model operations.
- Job execution and status tracking need careful design.
- More moving pieces than pure Next.js or pure Python.
- Direct model iteration may be slightly less ergonomic than a Python-first service.

### Best Fit

Best if SSR app experience is the top priority and Python model jobs are treated as background tasks.

### Risk

The system may split business logic between Next.js and Python unless boundaries are explicit.

## Option 5: Local-First Event-Driven Pipeline

### Shape

```text
Browser / CLI
  -> API or command trigger
      -> queue / event table
          -> ingestion worker
          -> sentiment worker
          -> forecast worker
          -> evaluation worker
      -> PostgreSQL
      -> local artifact storage
```

Possible queue choices:

- PostgreSQL job table for MVP.
- Redis Queue, Celery, Dramatiq, or Arq later.
- Filesystem inbox/outbox for very local experiments.

### Pros

- Strong fit for pipeline reliability and auditability.
- Each forecast run can be tracked step by step.
- Natural path to multi-ticker/watchlist batch processing later.
- Good for retries, provider failures, and long-running model jobs.
- Encourages clean data lineage.

### Cons

- More architecture than required for the first manual single-ticker MVP.
- Harder to build a simple user experience quickly.
- Requires job state management from the beginning.
- More operational complexity on a home server.

### Best Fit

Best after the basic pipeline proves useful and you want scheduled watchlists, batch evaluations, or multi-step model processing.

### Risk

Premature queue/pipeline abstractions can slow down the first end-to-end result.

## Recommendation

Use **Option 2: Next.js + FastAPI** for the main MVP.

### Why

This option fits the real risk profile of micromarket:

- The hardest work is data ingestion, sentiment quality, forecast evaluation, and explainability.
- Python should own the model/data path because it reduces friction.
- Jupyter notebooks should support exploratory data science, baseline tuning, and evaluation analysis without becoming part of the production runtime.
- Next.js gives you the SSR product shell you want without forcing the ML pipeline into Node.js.
- It keeps Go optional instead of mandatory.
- It supports local-only deployment now and home-server deployment later.
- It can grow toward watchlists and service boundaries without starting as a distributed system.

### Recommended Initial Boundaries

```text
Next.js
- UI routes
- server-side rendering
- form actions / API client
- display state
- light orchestration only

FastAPI
- ticker analysis API
- article upload and URL ingestion API
- sentiment pipeline
- forecast pipeline
- snapshot API
- evaluation API

Jupyter notebooks
- market-data exploration
- sentiment baseline inspection
- forecast-weight calibration
- model evaluation reports

PostgreSQL
- tickers
- articles
- article ingestions
- sentiment runs
- forecast runs
- snapshots
- evaluation outcomes

Local filesystem
- raw uploaded text
- fetched article HTML/text
- generated model artifacts
- experiment outputs
```

### Go Positioning

Do not add Go to the MVP critical path yet.

Add Go later if one of these becomes true:

- You need a stable public API gateway.
- You need high-concurrency provider orchestration.
- You need long-running daemon processes where Go's operational profile helps.
- You want to separate a durable service layer from experimental Python model code.

Until then, Go would likely add complexity without improving the accuracy or explainability goals.

## Recommended MVP Architecture

```text
micromarket/
  apps/
    web/                  # Next.js SSR UI
  services/
    api/                  # FastAPI backend
  packages/
    shared-contracts/     # Optional generated/openapi types later
  notebooks/              # Exploratory data science, not production runtime
  data/
    raw/                  # local raw article text/html
    artifacts/            # model outputs, experiment artifacts
    reports/              # notebook/evaluation reports
  infra/
    docker-compose.yml    # PostgreSQL + app services
  docs/
```

### Runtime Components

```text
User
  -> Next.js web app
      -> FastAPI `/analyses`
          -> article ingestion
          -> sentiment scoring
          -> forecast scoring
          -> PostgreSQL records
          -> local artifact writes
      <- analysis result
  <- dashboard
```

## MVP API Surface

### Analysis

- `POST /analyses`
  - Input: ticker, horizon, article text or URLs.
  - Output: analysis id, status, summary result.

- `GET /analyses/{analysis_id}`
  - Output: full analysis result, sentiment, forecast, evidence, limitations.

### Articles

- `POST /articles/text`
  - Input: ticker, title, source, published date, raw text.

- `POST /articles/url`
  - Input: ticker, URL.

### Forecasts

- `GET /forecasts/{forecast_id}`
  - Output: forecast details, confidence, model version, evidence links.

### Evaluation

- `POST /evaluations/refresh`
  - Updates actual outcomes for eligible old forecasts.

- `GET /evaluations/summary`
  - Returns model performance against baseline.

## Forecast Horizon Recommendation

For MVP, use **multiple stored horizons but one primary UI horizon**:

- Store: next close, 3 trading days, 7 trading days.
- Display primary: 3 trading days.

Reason:

- Next close may be too noisy and hard to attribute to article sentiment.
- 30 days introduces too many non-article variables.
- 3 trading days is short enough for news sentiment to matter but long enough to avoid pretending intraday precision.
- Storing multiple horizons allows later evaluation without rebuilding the data model.

## Market Data Provider Recommendation

Start with `yfinance` for MVP experimentation, with a provider interface that can later support Alpha Vantage, Finnhub, Polygon, or another paid provider.

### Why `yfinance` First

- Free and fast to prototype.
- Good enough for historical prices, ETFs, and many US equities.
- Works well for local research workflows.

### Caveat

Do not design the system as if `yfinance` is production-grade. Wrap it behind a `MarketDataProvider` interface from the start.

## Model Strategy Recommendation

Start with a baseline and evaluation loop:

1. Sentiment extraction:
   - MVP: LLM-assisted sentiment or local FinBERT-style model if easy to install.
   - Store raw sentiment result, confidence, evidence snippets, and model version.

2. Forecast baseline:
   - Rule-based weighted score combining:
     - article sentiment,
     - article count,
     - source agreement,
     - recency,
     - market momentum,
     - recent volatility.

3. Evaluation:
   - Compare against naive baselines:
     - no-change baseline,
     - recent momentum baseline,
     - random/majority direction baseline.

4. Retrospective:
   - Store why a forecast was made.
   - Later compare forecast confidence to actual outcome.

## Data Storage Recommendation

Use PostgreSQL for structured records:

- ticker metadata,
- article metadata,
- ingestion runs,
- sentiment runs,
- forecast runs,
- snapshots,
- evaluation outcomes.

Use local filesystem for raw artifacts:

- uploaded text,
- extracted article text,
- raw HTML if fetched,
- model artifacts,
- experiment reports.

Add S3-compatible archive later:

- MinIO for local S3-compatible storage, or
- AWS S3 when paid cloud use becomes acceptable.

## Why Not Start With Full Microservices

The desired final architecture may eventually involve multiple services. The MVP should avoid that until there is a measured need.

Starting with Next.js + FastAPI gives enough separation:

- UI is separate from data/model API.
- API contracts can stabilize.
- Python model internals can change without UI rewrites.
- Future Go services can be added behind the same API boundaries.

## Decision Summary

Recommended path:

1. Build with Next.js + FastAPI.
2. Use PostgreSQL.
3. Store raw artifacts locally.
4. Add Jupyter notebooks as a research workspace for data inspection, baseline tuning, and evaluation.
5. Use `yfinance` behind a provider interface.
6. Start with manual text upload and pasted URLs.
7. Use 3 trading days as the primary forecast horizon.
8. Store next-close and 7-day forecasts too for evaluation.
9. Keep Go out of MVP but reserve service boundaries for later.

## Next Documents To Create

- `09-technical-architecture.md`
- `10-data-model.md`
- `11-model-evaluation-plan.md`
- `12-implementation-roadmap.md`
