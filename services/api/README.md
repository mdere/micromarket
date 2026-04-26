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
artifacts, and returns the stored analysis/article metadata. Sentiment,
forecasting, market data, URL extraction, and evaluation routes are still
scaffold-level or provider-interface work.

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

The next backend milestone is adding SQLAlchemy models, Alembic migrations, and
real manual article analysis persistence.

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
