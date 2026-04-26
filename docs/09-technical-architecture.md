# micromarket Technical Architecture

## Architecture Decision

micromarket MVP will use:

- Next.js for the server-rendered web UI.
- FastAPI/Python for ingestion, sentiment, forecasting, and evaluation APIs.
- PostgreSQL for structured application and model-run data.
- Local filesystem storage for raw article text, fetched article content, model artifacts, and evaluation reports.
- Optional S3-compatible archive later.

Go is intentionally deferred. It can be added later for a stable API gateway, high-concurrency provider orchestration, or durable daemon services once those needs are measured.

## System Shape

```text
User
  -> Next.js web app
      -> FastAPI backend
          -> article ingestion
          -> URL extraction
          -> sentiment scoring
          -> forecast scoring
          -> evaluation refresh
          -> PostgreSQL
          -> local artifact storage
```

## Repository Layout

```text
micromarket/
  apps/
    web/
      app/
      components/
      lib/
      package.json
  services/
    api/
      app/
        api/
        core/
        db/
        ingestion/
        market_data/
        sentiment/
        forecasting/
        evaluation/
        storage/
      tests/
      pyproject.toml
  data/
    raw/
    processed/
    artifacts/
    reports/
  infra/
    docker-compose.yml
    env.example
  docs/
```

## Component Responsibilities

### Next.js Web App

Responsibilities:

- Render dashboard and forms.
- Provide ticker/article submission UI.
- Display analysis state, forecast, sentiment, evidence, and limitations.
- Call FastAPI endpoints.
- Keep UI language research-only and non-advisory.

Non-responsibilities:

- No direct model execution.
- No provider API secrets in frontend.
- No market-data provider logic.
- No forecast logic.

### FastAPI Backend

Responsibilities:

- Validate requests.
- Normalize ticker, article, and forecast inputs.
- Manage analysis workflow.
- Run article text ingestion and URL extraction.
- Fetch market data through provider interfaces.
- Run sentiment pipeline.
- Run baseline forecast pipeline.
- Persist all run metadata.
- Provide evaluation endpoints.

### PostgreSQL

Responsibilities:

- Store structured data.
- Preserve run lineage and model versions.
- Enable retrospective evaluation.
- Support future watchlist/multi-ticker expansion.

### Local Filesystem Storage

Responsibilities:

- Store raw uploaded text.
- Store fetched article HTML/text.
- Store generated summaries or extraction artifacts if needed.
- Store model artifacts and evaluation reports.

Structured database rows should point to artifact paths rather than storing large raw text blobs everywhere.

## MVP Runtime Flow

### Manual Text Analysis

1. User enters ticker and article text.
2. Next.js sends request to `POST /analyses`.
3. FastAPI validates ticker.
4. FastAPI stores raw article text artifact.
5. FastAPI creates article and ingestion records.
6. FastAPI fetches market data.
7. FastAPI scores sentiment and evidence.
8. FastAPI generates forecast and confidence.
9. FastAPI stores full analysis lineage.
10. Next.js renders the result.

### Pasted URL Analysis

1. User enters ticker and article URL.
2. FastAPI fetches URL content.
3. FastAPI extracts readable article text.
4. FastAPI stores raw and extracted artifacts.
5. Pipeline continues through sentiment, forecast, persistence, and display.

## API Surface

### Health

- `GET /health`
  - Returns API status and version.

### Analyses

- `POST /analyses`
  - Creates a ticker analysis from article text, URLs, or both.
  - MVP can run synchronously.
  - Later can return `queued` and support background jobs.

- `GET /analyses/{analysis_id}`
  - Returns analysis summary, forecast, sentiment, evidence, and limitations.

- `GET /analyses`
  - Lists recent analyses.

### Articles

- `POST /articles/text`
  - Stores manually supplied article text.

- `POST /articles/url`
  - Fetches and stores extracted article text from a URL.

- `GET /articles/{article_id}`
  - Returns article metadata and extracted content summary.

### Forecasts

- `GET /forecasts/{forecast_id}`
  - Returns forecast details, confidence, horizon, factors, and evidence.

### Evaluation

- `POST /evaluations/refresh`
  - Refreshes actual outcome data for eligible forecasts.

- `GET /evaluations/summary`
  - Returns model performance against baselines.

## Provider Interfaces

### Market Data Provider

Initial implementation: `yfinance`.

Interface should support:

- `get_quote(ticker)`
- `get_price_history(ticker, start, end)`
- `get_company_profile(ticker)`
- `get_etf_profile(ticker)`

The rest of the system should not depend directly on `yfinance` types.

### Article Extraction Provider

Initial implementation:

- Manual text input.
- URL extraction using maintained Python libraries.

Interface should support:

- `extract_from_url(url)`
- `normalize_article_text(raw_text)`
- `detect_language(text)`
- `estimate_readability(text)`

### Sentiment Provider

Initial implementation can be:

- LLM-assisted extraction if API access is available.
- FinBERT/local model if practical on the home server.
- Rule-based fallback for tests.

Interface should support:

- `score_article(article_text, ticker_context)`
- `score_batch(articles, ticker_context)`

Output must include:

- sentiment label,
- numeric score,
- confidence,
- drivers,
- evidence snippets,
- model/provider version.

## Forecast Strategy

Primary UI horizon: 3 trading days.

Stored horizons:

- next close,
- 3 trading days,
- 7 trading days.

The forecast service should generate separate forecast records per horizon. MVP can display only the 3-trading-day output while retaining other horizons for evaluation.

## Security

- Store secrets in environment variables.
- Never expose provider keys to Next.js client components.
- Keep API private/local for MVP.
- Sanitize URL inputs.
- Limit fetched URL size and request timeout.
- Avoid storing personal financial context in MVP.

## Deployment

MVP local deployment should use Docker Compose:

- `web`: Next.js app.
- `api`: FastAPI service.
- `db`: PostgreSQL.
- Optional `pgadmin` or admin tooling later.

Local development can run services directly before containerization if faster.

## Observability

Log:

- analysis request id,
- ticker,
- provider call status,
- ingestion failures,
- sentiment model version,
- forecast model version,
- latency per pipeline stage,
- limitation flags.

Avoid logging:

- API keys,
- full article text unless explicitly stored as an artifact,
- personal financial context.

## Architecture Guardrails

- Keep all model outputs versioned.
- Keep all forecasts reproducible from stored inputs where possible.
- Keep UI copy research-only.
- Build provider interfaces before adding multiple providers.
- Avoid background queue infrastructure until synchronous analysis becomes too slow or unreliable.
