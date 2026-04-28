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

The first UI slice supports creating analyses from manual article text or a URL,
selecting recent analyses, and viewing forecast, sentiment, market quote,
evidence, and limitation metadata.

Next UI direction: refactor the flat recent-analysis experience into
ticker-centered history. A selected ticker, such as AMD, should show all prior
AMD analysis runs and the articles/evidence used across those runs while
keeping every individual analysis traceable.
