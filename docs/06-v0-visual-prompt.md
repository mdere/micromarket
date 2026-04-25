# v0 Visual Generation Prompt: micromarket MVP

Use this prompt with a visual frontend generator to create the MVP dashboard shell.

## Prompt

Build a production-quality web app interface for `micromarket`, an AI-assisted stock research dashboard. The app helps users enter a stock ticker, ingest recent company articles, analyze sentiment, view stock-market metrics, and inspect an explainable short-term forecast. The product is decision-support software, not financial advice.

### Overall Theme and Mood

Create a dense, analytical research workspace. It should feel credible, calm, and data-focused, similar to a lightweight financial research terminal. Avoid marketing-page composition. The first screen should be the usable dashboard.

### Layout and Spacing

Use a responsive dashboard layout:

- Top navigation bar with product name, ticker search, refresh action, and snapshot link.
- Left column for company profile and market metrics.
- Center column for sentiment summary, forecast range, confidence, and risk flags.
- Right column for article evidence and model explanation.
- Lower full-width area for article table and snapshot history.

Use compact spacing, clear section headers, stable card dimensions, and tabular numeric alignment.

### Color Palette

Use a neutral base with restrained signal colors:

- Neutral background: off-white or very light gray.
- Text: near-black and slate gray.
- Positive signals: green.
- Negative signals: red.
- Neutral/uncertain signals: amber or gray.
- Use color plus text labels and icons so meaning does not depend on color alone.

### Typography

Use a readable sans-serif font. Use compact headings inside cards. Use tabular numerals for price, percentage, confidence, volume, and market-cap values.

### Icons

Use common interface icons:

- Search for ticker input.
- Refresh for re-run analysis.
- Save for snapshot.
- External link for article URLs.
- Trending up/down and minus/neutral for forecast direction.
- Alert for risk flags.
- Info for tooltips.

### Required Views

#### Dashboard Empty State

Route: `/`

Components:

- Ticker search input.
- Short dashboard placeholder.
- Recent snapshot list if available.
- Financial-risk disclaimer.

#### Dashboard Loading State

Components:

- Step progress list: validating ticker, fetching market data, ingesting articles, scoring sentiment, generating forecast.
- Skeleton cards for metrics and evidence table.

#### Dashboard Populated State

Components:

- Company header with ticker, name, exchange, latest price, daily change, and data timestamp.
- Forecast card with direction, estimated percent movement range, confidence, horizon, and model version.
- Sentiment card with aggregate score, article count, positive/neutral/negative split, and top drivers.
- Market metrics card with price, volume, market cap, 52-week range, moving averages, volatility proxy, beta, P/E, and analyst consensus placeholders.
- Risk flags card for low confidence, stale data, sparse articles, or conflicting signals.
- Article evidence table with title, source, date, sentiment, relevance, driver tags, and external link.
- Explanation panel listing top forecast factors.
- Save Snapshot button.

#### Snapshot History

Route: `/snapshots`

Components:

- Table of saved snapshots by ticker, timestamp, sentiment, forecast direction, confidence, and actual outcome placeholder.
- Filters for ticker and date range.

#### Snapshot Detail

Route: `/snapshots/:id`

Components:

- Read-only version of the dashboard at the saved timestamp.
- Model version and data lineage section.
- Article evidence used for that snapshot.

### Interactivity

- Ticker search submits with Enter and button click.
- Refresh reruns analysis.
- Save Snapshot is disabled while analysis is loading.
- Article rows expand to show sentiment summary and model-relevant details.
- Confidence, beta, P/E, moving averages, and model version have accessible info tooltips.
- Error states are inline and actionable.

### Accessibility

- Ensure keyboard navigation for all controls.
- Use text labels with icons.
- Maintain WCAG AA contrast.
- Provide meaningful table headers.
- Do not rely on green/red alone for positive/negative signals.

### Technical Notes

Generate React components with clean separation:

- `AppShell`
- `TickerSearch`
- `CompanyHeader`
- `ForecastCard`
- `SentimentSummary`
- `MarketMetrics`
- `RiskFlags`
- `ArticleEvidenceTable`
- `ExplanationPanel`
- `SnapshotHistory`
- `Disclaimer`

Use mock data for the initial generated UI. Keep components ready to connect to backend API responses later.
