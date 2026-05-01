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

Create a sample URL-based analysis:

```bash
curl -X POST http://localhost:8000/analyses \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "SPY",
    "articles": [
      {
        "url": "https://example.com/market-commentary"
      }
    ]
  }'
```

Some publishers block automated extraction or require an authenticated browser
session. If a URL-only run returns a message that the publisher blocked
extraction with HTTP `401` or `403`, paste the article text manually and include
the URL as source context instead. Manual text takes precedence when both text
and URL are supplied.

The response should include:

- persisted article metadata,
- a `market_quote` snapshot from `yfinance`,
- one baseline `sentiment_runs` record,
- one `sentiment_aggregate` summary,
- three baseline `forecast_runs` records for next close, 3 trading days, and
  7 trading days.

Article metadata includes `relevance_score`, `duplicate_group_id`,
`included_in_forecast`, and `exclusion_reason` so weak or duplicate evidence can
be audited.

If `POST /analyses` returns a provider error, confirm your network can reach
Yahoo Finance through `yfinance`. Unit tests use a fake provider and do not need
network access.

## Environment

Settings are read from process environment variables and local `.env` files via
`app/core/config.py`. Process environment values win. For manual API runs, copy
the checked-in example and edit the ignored local file:

```bash
cp services/api/.env.example services/api/.env
```

The API will read `services/api/.env` whether you start `uvicorn` from the
repository root or from `services/api`.

Useful defaults in `services/api/.env.example`:

```bash
MICROMARKET_ENV=local
DATABASE_URL=postgresql+psycopg://micromarket:micromarket@localhost:5432/micromarket
ARTIFACT_ROOT=./data
CORS_ORIGINS=http://localhost:3000
MARKET_LOOKBACK_DAYS=30
SENTIMENT_PROVIDER=baseline
SENTIMENT_PROVIDER_FALLBACK=baseline
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_SENTIMENT_MODEL=llama3.1:8b
OLLAMA_TIMEOUT_SECONDS=30
```

For Docker Compose, copy the Compose environment example:

```bash
cp infra/.env.example infra/.env
```

`infra/.env` points `DATABASE_URL` at the Compose database service. It is
ignored by Git.

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
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up --build
```

The API container mounts the repository `data/` directory at `/app/data`, which
matches `ARTIFACT_ROOT=/app/data` in `infra/.env.example`.

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
- `GET /analyses?ticker=SPY`
- `POST /evaluations/refresh`
- `GET /evaluations/summary`

The analysis route now persists manual text submissions, stores article text
and URL-extracted submissions, stores article artifacts, fetches a `yfinance`
market quote through the provider interface,
persists the quote snapshot, scores article sentiment with the baseline
provider, persists sentiment runs and an aggregate, creates baseline forecast
runs, and returns stored analysis/article/quote/sentiment/forecast metadata.
Analysis responses include creation/completion timestamps and failed-run error
messages, and list responses can be filtered by ticker for ticker-scoped UI
history.
Evaluation refresh can persist outcomes for expired forecast runs.

Run database migrations from `services/api`:

```bash
alembic upgrade head
```

Import reviewed entity seed definitions after migrations:

```bash
python -m app.ingestion.seed_entities
```

The checked-in bootstrap snapshot is `app/ingestion/entity_seed_snapshot.json`.
It is an idempotent import into the local DB-backed entity seed registry; rerun
it when the reviewed seed snapshot changes.

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
- The initial URL extraction implementation is `app/ingestion/url_provider.py`.

The next backend milestone is a minimal UI over the stable API response.

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
| `yf_ticker.history(start=..., end=..., interval="1d", auto_adjust=False)` | `Ticker.history()` | Historical close lookup for evaluating expired forecasts. | <https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html> |

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

`volume` and `market_cap` are stored as 64-bit integers because live market data
can exceed PostgreSQL's 32-bit integer range.

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

## Sentiment Providers

The default MVP sentiment provider is `BaselineSentimentProvider` in
`app/sentiment/baseline.py`. Provider selection is controlled by
`SENTIMENT_PROVIDER` and happens in `app/sentiment/dependencies.py`.

It is intentionally deterministic and transparent. It uses a small positive and
negative financial-language lexicon to produce:

- `sentiment_label`: `positive`, `neutral`, `negative`, or `mixed`
- `sentiment_score`: normalized from `-1.0` to `1.0`
- `confidence_score`: bounded confidence based on matched signal density,
  uncertainty, mixed evidence, and article length
- `drivers`: finance-specific categories such as earnings, guidance, demand,
  valuation, macro, regulatory, supply, product, and uncertainty
- `evidence_snippets`: up to three matching sentences
- `limitations`: notes such as no matched terms or very short text
- `model_name` and `model_version`

During `POST /analyses`, the API stores one `sentiment_runs` row per article and
one `sentiment_aggregates` row for the analysis. The aggregate stores article
counts, positive/neutral/negative/mixed counts, aggregate score, agreement
score, evidence-strength score, and a short summary. Duplicate or low-relevance
articles still receive sentiment runs for lineage, but excluded evidence is not
included in the aggregate sentiment used by forecasts.

This baseline is not intended to be the final model. It gives the project a
repeatable measurement floor before introducing FinBERT, LLM-assisted sentiment,
or a custom model. Future providers should continue to satisfy the local
`SentimentProvider` protocol and store model/provider versions with every run.

Curated sentiment fixtures live at
`tests/fixtures/sentiment_curated_examples.json`. Use those fixtures to compare
provider behavior before trusting prompt or model intuition.

Before those comparisons are trusted, the API should support as-of-time aligned
historical replay. A historical article published on `2026-03-05` should be
analyzed with market features available around `2026-03-05`, with forecast
targets starting from that date, even if the article is ingested later.

The same foundation should backfill ticker context. When a new ticker is first
analyzed, the API should store a configurable historical market window, such as
30 days, and preserve related entities extracted from articles. For example, an
`NVDA` article mentioning `TSMC`, `Samsung`, or `HBM` should keep those
relationships so later analyses can compare related narratives with market
movement.

`MARKET_LOOKBACK_DAYS` controls the market-history window used during analysis
creation and defaults to `30`. `POST /analyses` now resolves `analysis_as_of`,
stores or refreshes daily market history for the ticker, and includes
feature-window metadata in forecast responses. If an article provides
`published_at`, that timestamp becomes the historical decision point unless the
request explicitly sets `analysis_as_of`.

Article ingestion also performs deterministic related-entity extraction. The
first pass uses an alias/theme dictionary and stores matches in `entities`,
`article_entities`, and `asset_relationships`. Article responses include
relationship type, confidence, evidence snippets, and provider/model lineage.
For example, an `NVDA` article mentioning `TSMC`, `Samsung`, `HBM`, or foundry
capacity will return those related entities with research-only relationship
metadata.

### Ollama Sentiment Provider

`OllamaSentimentProvider` in `app/sentiment/ollama_provider.py` is an optional
local LLM provider behind the same `SentimentProvider` protocol. It is disabled
by default and does not run in tests unless fake HTTP responses are injected.

Use it when you want to compare a local LLM sentiment read against the
deterministic baseline. Keep `SENTIMENT_PROVIDER_FALLBACK=baseline` on while
experimenting so analysis creation can still complete if Ollama is unavailable
or returns invalid JSON.

#### 1. Install Ollama

On macOS, either install the desktop app from <https://ollama.com/download> or
use Homebrew:

```bash
brew install ollama
```

On Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify the CLI is available:

```bash
ollama --version
```

#### 2. Start Ollama And Pull A Model

Start the local Ollama server in a separate terminal:

```bash
ollama serve
```

Then pull the default project model:

```bash
ollama pull llama3.1:8b
```

You can use another local chat model later by changing `OLLAMA_SENTIMENT_MODEL`,
but keep `llama3.1:8b` as the first smoke-test target because the docs and
fixtures assume it.

Confirm Ollama can respond:

```bash
ollama run llama3.1:8b "Return only JSON: {\"status\":\"ok\"}"
```

You can also check the HTTP API directly:

```bash
curl http://localhost:11434/api/tags
```

#### 3. Configure The API

For local API runs, edit `services/api/.env`:

```bash
SENTIMENT_PROVIDER=ollama
SENTIMENT_PROVIDER_FALLBACK=baseline
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_SENTIMENT_MODEL=llama3.1:8b
OLLAMA_TIMEOUT_SECONDS=30
```

Then start the API normally:

```bash
cd services/api
source .venv/bin/activate
uvicorn app.main:app --reload
```

For Docker Compose, edit `infra/.env`.
If the API runs in a container and Ollama runs on the host, `localhost` inside
the container points at the container, not your host. On Docker Desktop for
macOS/Windows, use:

```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434/api
```

On Linux Docker, either run the API locally outside Docker for the first smoke
test or configure host networking / a reachable host address for Ollama.

#### 4. Smoke Test Through The API

With PostgreSQL and the API running, submit a manual analysis:

```bash
curl -X POST http://localhost:8000/analyses \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AMD",
    "articles": [
      {
        "title": "AMD local Ollama sentiment smoke test",
        "source": "manual note",
        "text": "AMD reported revenue growth and raised guidance as AI accelerator demand improved. Analysts also noted valuation concerns and supply constraints."
      }
    ]
  }'
```

Inspect `sentiment_runs[0]` in the response:

- `provider: "ollama"` means Ollama produced valid structured sentiment.
- `provider: "baseline"` plus a limitation containing `Ollama sentiment provider
  failed` means fallback worked and the run still completed.
- A `502` response means fallback is disabled or unavailable and the provider
  error was allowed to fail the analysis.

The provider calls Ollama's `/chat` endpoint with JSON output required. It
validates that the model returns `label`, `score`, `confidence`, `drivers`,
`evidence_snippets`, and `limitations`. Invalid JSON, missing fields, provider
HTTP errors, and timeouts raise clear `SentimentProviderError` values. When
`SENTIMENT_PROVIDER_FALLBACK=baseline`, those failures return baseline
sentiment with an explicit limitation noting the Ollama failure.

The prompt is limited to research-only article sentiment and evidence
extraction. It does not ask for direct investment decisions.

#### 5. Compare Against Fixtures

Open `notebooks/02_sentiment_baseline.ipynb` and set:

```python
RUN_OLLAMA_COMPARISON = True
```

Run the curated fixture comparison cells to compare baseline and Ollama labels,
scores, drivers, and confidence. Keep this exploratory; promote only stable
findings into backend code and tests.

The comparison roadmap is documented in
`../../docs/13-model-quality-plan.md#baseline-vs-ollama-comparison-workflow`.
Use that workflow to track label accuracy, driver coverage, evidence snippet
quality, runtime, fallback rate, and whether Ollama improves enough to justify
changing defaults later.

You can also generate review files without opening Jupyter:

```bash
cd services/api
source .venv/bin/activate
python -m app.sentiment.comparison --include-ollama
```

For slower local CPU runs, compare a smaller batch first:

```bash
python -m app.sentiment.comparison --include-ollama --limit 5
python -m app.sentiment.comparison --include-ollama --fixture-id mixed_partner_strength_customer_delay
python -m app.sentiment.comparison --include-ollama \
  --fixture-id mixed_partner_strength_customer_delay \
  --fixture-id mixed_earnings_beat_guidance_cut
```

When diagnosing timeouts, disable fallback for a single fixture so the report
shows a native Ollama result or a native Ollama error instead of a baseline
substitute:

```bash
python -m app.sentiment.comparison --include-ollama --ollama-no-fallback \
  --ollama-timeout-seconds 300 \
  --fixture-id mixed_earnings_beat_guidance_cut
```

You can also override the model without editing `.env`, which is useful when
trying a smaller local model:

```bash
python -m app.sentiment.comparison --include-ollama --ollama-no-fallback \
  --ollama-model llama3.2:3b \
  --ollama-timeout-seconds 180 \
  --fixture-id mixed_earnings_beat_guidance_cut
```

Outputs:

- `../../data/reports/sentiment_provider_comparison.csv`
- `../../data/reports/sentiment_provider_comparison.md`
- `../../data/reports/sentiment_provider_review.md`

The CSV and review Markdown include blank review fields for `snippet_quality`,
`driver_quality`, `research_only`, `review_notes`, and `review_action`. Use the
review Markdown for VS Code-friendly row-by-row inspection, then promote stable
findings back into fixtures, provider tests, prompt changes, or parser changes.

## URL Ingestion

`POST /analyses` accepts either manual article text or an absolute `http(s)`
article URL for each submitted article. Manual `text` takes precedence when both
`text` and `url` are present.

The MVP URL extractor uses `trafilatura` behind the local
`URLExtractionProvider` protocol in `app/ingestion/url_provider.py`.
`trafilatura` is used for readable main-text extraction and metadata such as
title and site name, while raw fetching is kept local with `httpx`. Extracted
article text is stored as a `.txt` artifact and raw fetched HTML is stored as a
`.html` artifact under the local artifact root.

URL extraction failures return a `502` response and mark the analysis as
`failed`. Tests inject a fake URL extraction provider and do not require network
access.

## Evidence Filtering

`POST /analyses` applies a deterministic first-pass evidence policy before
building aggregate sentiment and forecasts:

- article text, title, and URL are scored for ticker relevance,
- duplicate content hashes are grouped,
- duplicate or low-relevance articles are persisted but excluded from forecast
  inputs,
- exclusion metadata is returned with article responses.

This is intentionally conservative and transparent rather than a final
relevance model. It gives later UI and notebook work enough lineage to inspect
why evidence did or did not influence a forecast.

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

This baseline is intentionally simple and has not been validated at scale yet.
It exists to preserve lineage and provide a repeatable measurement floor for
the evaluation loop.

## Evaluation Refresh

`POST /evaluations/refresh` finds forecast runs whose target end time has passed
and that do not yet have a `forecast_outcomes` row. For each eligible forecast,
it asks the market-data provider for the first available daily close on or after
the target date, then stores:

- actual end price,
- actual percent change,
- actual direction,
- directional correctness,
- absolute error,
- no-change baseline correctness and error.

`GET /evaluations/summary` returns total evaluated forecasts and per-horizon
summary metrics. Tests inject a fake market-data provider so evaluation stays
offline and deterministic.

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
