# micromarket API

FastAPI backend for micromarket ingestion, sentiment, forecasting, market data, and
evaluation.

The API is local-first. It is intended to run beside PostgreSQL and local artifact
storage during MVP development.

## Prerequisites

- Python 3.10 or newer
- `pip` and `venv`
- Docker Compose, if you want PostgreSQL managed for you
- Network access for the first dependency install

The local package currently supports Python 3.10+. The Docker image uses Python
3.12.

## Quick Start

From the repository root, start PostgreSQL:

```bash
docker compose -f infra/docker-compose.yml up -d db
```

Set up and run the API:

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

The API will listen on `http://localhost:8000`.

In another terminal, verify it:

```bash
curl http://localhost:8000/health
```

Create a sample analysis:

```bash
curl -X POST http://localhost:8000/analyses \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "SPY",
    "articles": [
      {
        "title": "SPY sample article",
        "source": "manual note",
        "text": "SPY saw improving breadth and resilient demand across large caps. Analysts described constructive momentum, although volatility risk remains."
      }
    ]
  }'
```

The response should include:

- persisted article metadata,
- a `market_quote` snapshot from `yfinance`,
- one baseline `sentiment_runs` record,
- one `sentiment_aggregate` summary,
- three baseline `forecast_runs` records for next close, 3 trading days, and
  7 trading days.

If `POST /analyses` returns a provider error, confirm your network can reach
Yahoo Finance through `yfinance`. Unit tests use a fake provider and do not need
network access.

## Environment

Settings are read from environment variables and, when running from this
directory, an optional `.env` file.

Useful defaults:

```bash
MICROMARKET_ENV=local
DATABASE_URL=postgresql+psycopg://micromarket:micromarket@localhost:5432/micromarket
ARTIFACT_ROOT=./data
CORS_ORIGINS=http://localhost:3000
```

For Docker Compose, use `infra/env.example`; it points `DATABASE_URL` at the
Compose database service.

## Local Setup

From the repository root:

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Start PostgreSQL from the repository root:

```bash
docker compose -f infra/docker-compose.yml up -d db
```

Then start the API:

```bash
cd services/api
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

The API will listen on `http://localhost:8000`.

## Docker Compose

To run PostgreSQL, API, and web together from the repository root:

```bash
docker compose -f infra/docker-compose.yml up --build
```

The API container mounts the repository `data/` directory at `/app/data`, which
matches `ARTIFACT_ROOT=/app/data` in `infra/env.example`.

## Verification

Health check:

```bash
curl http://localhost:8000/health
```

Expected response shape:

```json
{
  "status": "ok",
  "service": "micromarket-api",
  "environment": "local",
  "version": "0.1.0"
}
```

Current API endpoints:

- `GET /health`
- `POST /analyses`
- `GET /analyses/{analysis_id}`
- `GET /analyses`
- `POST /evaluations/refresh`
- `GET /evaluations/summary`

The analysis route now persists manual text submissions, stores article text
artifacts, fetches a `yfinance` market quote through the provider interface,
persists the quote snapshot, scores article sentiment with the baseline
provider, persists sentiment runs and an aggregate, creates baseline forecast
runs, and returns stored analysis/article/quote/sentiment/forecast metadata.
URL extraction and evaluation routes are still scaffold-level or
provider-interface work.

Run database migrations from `services/api`:

```bash
alembic upgrade head
```

## Tests And Linting

Run tests:

```bash
cd services/api
source .venv/bin/activate
python -m pytest
```

Run Ruff:

```bash
python -m ruff check app tests
```

## Development Notes

- `app/main.py` builds the FastAPI app.
- `app/api/router.py` wires route modules.
- `app/core/config.py` owns environment configuration.
- `app/db/session.py` owns SQLAlchemy engine/session setup.
- Provider protocols live under `app/market_data`, `app/sentiment`, and
  `app/forecasting`.
- The initial market-data implementation is `app/market_data/yfinance_provider.py`.
- The initial sentiment implementation is `app/sentiment/baseline.py`.
- The initial forecast implementation is `app/forecasting/baseline.py`.

The next backend milestone is adding an evaluation refresh path that can compare
expired forecast runs against actual outcomes and naive baselines.

## Market Data Provider

The MVP market-data provider is `YFinanceMarketDataProvider` in
`app/market_data/yfinance_provider.py`.

The rest of the API depends on the local `MarketDataProvider` protocol in
`app/market_data/provider.py`, not directly on `yfinance`. Routes receive the
provider through `app/market_data/dependencies.py`, which lets tests inject a
fake provider and keeps unit tests offline.

### Runtime Flow

During `POST /analyses`:

1. The route normalizes the submitted ticker.
2. It calls `market_data_provider.get_quote(ticker)`.
3. The `yfinance` provider returns a normalized `MarketQuote` dataclass.
4. The route persists that snapshot in `market_quotes`, linked to the analysis
   through `market_quotes.analysis_id`.
5. The response includes a compact `market_quote` object with provider, price,
   previous close, open/high/low, volume, market cap, quote time, and retrieval
   time.

Provider failures return a `502` response and mark the analysis as `failed`.

### yfinance API Calls

The implementation intentionally uses a small subset of `yfinance`:

| Provider code | yfinance API | Purpose | Reference |
| --- | --- | --- | --- |
| `yf.Ticker(symbol)` | `yfinance.Ticker` | Creates a single-symbol Yahoo Finance ticker object. | <https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html> |
| `yf_ticker.fast_info` | `Ticker.fast_info` | Primary lightweight source for current quote fields when available. | <https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.fast_info.html> |
| `yf_ticker.info` | `Ticker.info` | Fallback and supplemental metadata source for market cap, averages, beta, P/E, and profile-like fields. | <https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.info.html> |
| `yf_ticker.history(period="5d", interval="1d", auto_adjust=False)` | `Ticker.history()` | Fallback source for latest OHLCV values and quote date when quote fields are missing. | <https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html> |

The normalized fields currently persisted are:

- `price`
- `previous_close`
- `open`
- `day_high`
- `day_low`
- `volume`
- `market_cap`
- `fifty_two_week_high`
- `fifty_two_week_low`
- `moving_average_50`
- `moving_average_200`
- `beta`
- `pe_ratio`
- `quote_time`
- `retrieved_at`

The provider should keep `yfinance` objects and field-name quirks contained
inside `app/market_data/yfinance_provider.py`. Downstream analysis, sentiment,
forecasting, and evaluation code should consume only local dataclasses and
database models.

### yfinance Caveats

`yfinance` is a good local-first MVP provider, but it is not treated as a
production-grade market-data contract. It uses Yahoo Finance data through the
open-source library, fields can be missing or renamed, and provider calls may
fail because of network or upstream data issues. For that reason:

- Keep all provider-specific logic behind `MarketDataProvider`.
- Store the provider name with every market quote.
- Let `None` represent missing fields instead of inventing values.
- Use deterministic fake providers in tests.
- Revisit the provider boundary before adding paid or higher-reliability data
  sources.

## Sentiment Provider

The MVP sentiment provider is `BaselineSentimentProvider` in
`app/sentiment/baseline.py`.

It is intentionally deterministic and transparent. It uses a small positive and
negative financial-language lexicon to produce:

- `sentiment_label`: `positive`, `neutral`, or `negative`
- `sentiment_score`: normalized from `-1.0` to `1.0`
- `confidence_score`: bounded confidence based on number of matched terms
- `drivers`: matched positive and negative term groups
- `evidence_snippets`: up to three matching sentences
- `limitations`: notes such as no matched terms or very short text
- `model_name` and `model_version`

During `POST /analyses`, the API stores one `sentiment_runs` row per article and
one `sentiment_aggregates` row for the analysis. The aggregate stores article
counts, positive/neutral/negative/mixed counts, aggregate score, agreement
score, evidence-strength score, and a short summary.

This baseline is not intended to be the final model. It gives the project a
repeatable measurement floor before introducing FinBERT, LLM-assisted sentiment,
or a custom model. Future providers should continue to satisfy the local
`SentimentProvider` protocol and store model/provider versions with every run.

## Forecast Provider

The MVP forecast provider is `BaselineForecastProvider` in
`app/forecasting/baseline.py`.

It consumes normalized quote fields and the persisted sentiment aggregate, then
creates forecast records for:

- `next_close`
- `3_trading_days`
- `7_trading_days`

Each `forecast_runs` record stores the provider, model name/version, predicted
direction, predicted percent change, confidence score, no-change baseline,
feature snapshot, top factors, limitations, target start price/time, and target
end time. Direction language is deliberately non-advisory: `up`, `down`, or
`uncertain`; no buy/sell/hold instruction is produced.

This baseline is intentionally simple and has not been evaluated yet. It exists
to preserve lineage and provide a repeatable measurement floor for the upcoming
evaluation loop.

## Troubleshooting

If `pip install -e ".[dev]"` fails because of Python version constraints, check:

```bash
python --version
```

Use Python 3.10 or newer.

If the API cannot connect to PostgreSQL, confirm the database is running and
that `DATABASE_URL` matches how you started it:

- Manual/local API: host should usually be `localhost`.
- Docker Compose API: host should be `db`.

If tests hang or HTTP checks fail inside a restricted sandbox, rerun them in a
normal local shell. FastAPI's test client and loopback HTTP checks require local
threading/network behavior that some sandboxes block.
