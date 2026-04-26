# micromarket Research Notebooks

This workspace is for exploratory data science during the MVP. It is not part of the production runtime.

Use notebooks to inspect data quality, tune baseline parameters, explore model behavior, and create reports. When a finding becomes part of the product, move the stable logic into tested modules under `services/api/app`.

## Setup

From the API package:

```bash
cd services/api
source .venv/bin/activate
python -m pip install -e ".[dev,notebooks]"
python -m ipykernel install --user --name micromarket-api --display-name "micromarket API"
```

Then start Jupyter from the repository root:

```bash
cd ../..
jupyter lab notebooks
```

Use the `micromarket API` kernel when opening these notebooks.

## Starter Notebooks

- `01_market_data_exploration.ipynb`: inspect `yfinance` quote/history data for MVP equities and ETFs.
- `02_sentiment_baseline.ipynb`: prototype transparent lexical sentiment scoring and evidence extraction.
- `03_forecast_baseline.ipynb`: tune a first weighted forecast formula using sentiment, evidence strength, momentum, and volatility.
- `04_evaluation_analysis.ipynb`: inspect forecast outcomes, confidence calibration, and baseline comparisons.

## Ground Rules

- Keep notebooks exploratory and repeatable.
- Do not commit secrets, API keys, local connection strings with credentials, or personal financial context.
- Save generated charts/reports under `data/reports`.
- Keep source-of-truth records in PostgreSQL and local artifacts, not in notebook-only variables.
- Promote stable logic into `services/api/app` with tests before the API depends on it.
