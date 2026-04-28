# micromarket Web

Next.js frontend for the micromarket research dashboard.

## Local Development

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

The dashboard calls `http://localhost:8000` by default. Override it with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

The dashboard supports creating analyses from manual article text or a URL,
loading a selected ticker workspace, selecting prior analyses for that ticker,
and viewing forecast, sentiment, market quote, evidence, and limitation
metadata. Article rows link back to the source URL when one is available. The
dashboard also shows persistent API/evidence notices and a model-monitoring
summary from `GET /evaluations/summary`. The evaluation monitor can trigger
`POST /evaluations/refresh` and reload the summary afterward.

Dashboard rendering is split into components under `components/dashboard`.
Shared API response types and formatting helpers live under `lib`. The
dashboard includes panel-level loading states and shows backend failure details
when failed analyses are available in ticker history.

Ticker-centered history is the active UI shape. A selected ticker, such as AMD,
shows prior AMD analysis runs and the articles/evidence used across those runs
while keeping every individual analysis traceable.
