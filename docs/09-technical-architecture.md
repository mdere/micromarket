# micromarket Technical Architecture

## Architecture Decision

micromarket MVP will use:

- Next.js for the server-rendered web UI.
- FastAPI/Python for ingestion, sentiment, forecasting, and evaluation APIs.
- Jupyter notebooks for exploratory data science, feature inspection, model calibration, and evaluation analysis.
- PostgreSQL for structured application and model-run data.
- Local filesystem storage for raw article text, fetched article content, model artifacts, and evaluation reports.
- Optional Ollama/local LLM sentiment provider behind a provider interface.
- Optional S3-compatible archive later.

Go is intentionally deferred. It can be added later for a stable API gateway, high-concurrency provider orchestration, or durable daemon services once those needs are measured.

Jupyter is part of the MVP development and research workflow, not the production runtime. Notebooks should read from PostgreSQL and local artifacts, produce exploratory reports or model parameters, and then promote stable logic into tested Python modules under `services/api/app`.

Ollama may be used as a local external model runtime for sentiment experiments. It should be optional, configurable, and accessed only through backend provider interfaces. The default runtime remains the deterministic baseline unless configuration selects another provider.

Historical analysis must be as-of-time aligned. The backend should resolve an `analysis_as_of` timestamp for every run and compute article eligibility, market lookbacks, forecast targets, and outcomes relative to that timestamp.

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
  notebooks/
    01_market_data_exploration.ipynb
    02_sentiment_baseline.ipynb
    03_forecast_baseline.ipynb
    04_evaluation_analysis.ipynb
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
- Resolve live or historical analysis as-of time.
- Manage analysis workflow.
- Run article text ingestion and URL extraction.
- Fetch market data through provider interfaces.
- Run sentiment pipeline.
- Select sentiment providers through configuration.
- Call optional local LLM providers such as Ollama through provider boundaries.
- Run baseline forecast pipeline.
- Persist all run metadata.
- Provide evaluation endpoints.

### Jupyter Notebooks

Responsibilities:

- Explore market data quality, coverage, gaps, and quirks from providers such as `yfinance`.
- Inspect article text normalization, duplicate detection, sentiment drivers, and evidence snippets.
- Prototype baseline sentiment and forecast formulas before moving stable code into `services/api/app`.
- Compare deterministic and local LLM sentiment providers against curated fixtures.
- Analyze forecast outcomes, confidence calibration, and model-vs-baseline performance.
- Generate local evaluation reports under `data/reports`.

Non-responsibilities:

- No production API endpoints.
- No hidden source of forecast logic that is not represented in versioned backend code.
- No manual database edits required for the app to work.
- No secrets or personal financial context committed to notebooks.

Hosted notebook environments such as Google Colab or Databricks can be used for exploratory model work when local compute is insufficient. They should operate on exported, sanitized datasets and should not become production dependencies.

### PostgreSQL

Responsibilities:

- Store structured data.
- Preserve run lineage and model versions.
- Enable retrospective evaluation.
- Support ticker-centered analysis history for repeated runs on the same asset.
- Support future watchlist/multi-ticker expansion.

### Local Filesystem Storage

Responsibilities:

- Store raw uploaded text.
- Store fetched article HTML/text.
- Store generated summaries or extraction artifacts if needed.
- Store model artifacts and evaluation reports.
- Store notebook-generated exploratory outputs and charts under `data/reports` or `data/artifacts`.

Structured database rows should point to artifact paths rather than storing large raw text blobs everywhere.

## MVP Runtime Flow

### Manual Text Analysis

1. User enters ticker and article text.
2. Next.js sends request to `POST /analyses`.
3. FastAPI validates ticker.
4. FastAPI resolves `analysis_as_of`, defaulting to live analysis time unless historical replay is requested.
5. FastAPI stores raw article text artifact.
6. FastAPI creates article and ingestion records.
7. FastAPI fetches market data available at or before `analysis_as_of`.
8. FastAPI scores sentiment and evidence.
9. FastAPI generates forecast and confidence using feature windows ending at `analysis_as_of`.
10. FastAPI stores full analysis lineage.
11. Next.js renders the result.

### Historical Replay Analysis

1. User or notebook submits ticker evidence with a historical article `published_at` timestamp or explicit `analysis_as_of`.
2. FastAPI rejects or excludes article evidence published after `analysis_as_of`.
3. FastAPI fetches a lookback window, such as the prior 30 days, ending at `analysis_as_of`.
4. FastAPI generates forecast target windows starting at `analysis_as_of`.
5. Evaluation later compares the stored forecast to actual prices after the target window.

This flow is required for model training and backtesting so the system does not learn from future prices or future article evidence.

### Data Science Workflow

1. FastAPI stores analyses, articles, sentiment runs, forecasts, outcomes, and artifact paths.
2. A notebook connects to the same local PostgreSQL database or reads exported data.
3. The notebook inspects data quality, model behavior, feature weights, confidence calibration, and baseline comparisons.
4. Useful findings become:
   - adjusted model parameters recorded in `model_versions`,
   - tested Python code in `services/api/app/sentiment`, `services/api/app/forecasting`, or `services/api/app/evaluation`,
   - evaluation reports saved under `data/reports`.
5. The API remains the source of truth for repeatable analysis execution.

### Local LLM Sentiment Workflow

1. User configures `SENTIMENT_PROVIDER=ollama` and an Ollama base URL/model.
2. FastAPI receives article evidence through the normal analysis flow.
3. `OllamaSentimentProvider` sends a structured sentiment prompt to the local Ollama API.
4. FastAPI validates the JSON response, maps it to the `SentimentProvider` contract, and persists the sentiment run with provider/model version.
5. If the provider fails, the API returns a clear provider error or uses an explicitly configured fallback.

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
  - Should support filtering by ticker/asset so the UI can load one ticker's analysis timeline without unrelated runs.

- `GET /tickers/{symbol}/analyses`
  - Optional clearer route for ticker-centered history if it fits the implementation better than query filtering.
  - Returns all analysis summaries for the selected ticker, newest first, with article counts and enough metadata for timeline navigation.

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
- `get_history_window(ticker, as_of, lookback_days)`
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

Initial implementation:

- `BaselineSentimentProvider`
  - local deterministic baseline,
  - transparent,
  - testable without network access.

Next target:

- `OllamaSentimentProvider`
  - optional local LLM-backed sentiment provider,
  - configured by environment,
  - structured JSON output only,
  - tested with fake provider responses.

Later implementations:

- FinBERT/local transformer if practical on the home server.
- OpenAI-compatible provider if intentionally enabled.

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

Forecast features should be computed from windows ending at the analysis `analysis_as_of` timestamp. Forecast target windows should start at `analysis_as_of`, not at ingestion time.

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
- Optional `notebooks` profile later for Jupyter if running notebooks on the home server is useful.

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
- Keep historical runs free of lookahead bias by honoring `analysis_as_of`.
- Keep UI copy research-only.
- Build provider interfaces before adding multiple providers.
- Avoid background queue infrastructure until synchronous analysis becomes too slow or unreliable.
