# micromarket Research Notebooks

This workspace is for exploratory data science during the MVP. It is not part of the production runtime.

Use notebooks to inspect data quality, tune baseline parameters, explore model behavior, and create reports. When a finding becomes part of the product, move the stable logic into tested modules under `services/api/app`.

The next model-quality workflow is sentiment-first: compare the deterministic baseline against curated fixtures, then optionally compare local LLM output from Ollama or hosted notebook experiments.

Historical experiments must be time-aligned. When reviewing an article from a past date, derive the analysis as-of timestamp from the article publish time or an explicit historical timestamp, use market lookbacks ending at that timestamp, and evaluate forecast targets after that timestamp.

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

Recommended next notebooks or notebook sections:

- sentiment fixture review: inspect hand-labeled examples and provider outputs,
- historical replay review: compare article publish dates, analysis as-of timestamps, market lookback windows, and target windows,
- baseline-vs-Ollama comparison: compare labels, scores, drivers, snippets, and confidence,
- hosted experiment export: run the same fixture comparison in Colab or Databricks if local compute is too slow.

## Ground Rules

- Keep notebooks exploratory and repeatable.
- Do not commit secrets, API keys, local connection strings with credentials, or personal financial context.
- Save generated charts/reports under `data/reports`.
- Keep source-of-truth records in PostgreSQL and local artifacts, not in notebook-only variables.
- Promote stable logic into `services/api/app` with tests before the API depends on it.
- Hosted notebooks may use exported sanitized datasets only.
- Do not make Colab, Databricks, or another hosted notebook a required runtime dependency.
