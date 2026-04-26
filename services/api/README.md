# micromarket API

FastAPI backend for micromarket ingestion, sentiment, forecasting, and evaluation.

## Local Development

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```
