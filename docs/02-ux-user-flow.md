# UX and User Flow Specification: micromarket

## 1. Information Architecture

### MVP Page Map

- `/` Research dashboard with ticker input and current result.
- `/snapshots` Saved research snapshots.
- `/snapshots/:id` Snapshot detail view.
- `/settings` Data-source and model configuration placeholder.

### Primary Layout Zones

- Top bar: product name, ticker search, refresh status, saved snapshots.
- Left panel: selected company profile and market metrics.
- Main panel: sentiment summary, forecast card, confidence and risk notes.
- Right panel: article evidence and model explanation.
- Bottom section: raw article table and snapshot history.

## 2. Core User Flows

### Flow A: Research a Ticker

1. User opens dashboard.
2. User enters a ticker.
3. System validates ticker.
4. System loads company and market data.
5. System ingests recent articles.
6. System runs sentiment and forecast pipeline.
7. Dashboard displays summary, forecast range, confidence, market metrics, and source evidence.
8. User drills into article evidence or saves a snapshot.

### Flow B: Review Evidence

1. User clicks a sentiment driver or evidence item.
2. Right panel opens article detail.
3. User sees source, date, sentiment score, relevance score, key excerpts or summary, and associated model factors.
4. User returns to dashboard without losing ticker state.

### Flow C: Save Snapshot

1. User clicks Save Snapshot.
2. System records current data, model version, and timestamp.
3. User sees confirmation and snapshot appears in history.
4. User can open snapshot detail later.

## 3. View Specifications

### Dashboard Empty State

- Prominent ticker search input.
- Compact explanation: "Enter a ticker to analyze recent sentiment and market signals."
- No investment advice language.
- Optional recent examples if local history exists.

### Dashboard Loading State

- Step indicators for ticker validation, market data, article ingestion, sentiment processing, and forecast generation.
- Partial data may appear as soon as available.
- Failures show precise recovery actions.

### Dashboard Populated State

- Company header: ticker, company name, exchange, current price, daily change, data timestamp.
- Forecast card: direction, estimated percent range, confidence, horizon, model version.
- Sentiment card: aggregate sentiment, article count, positive/neutral/negative split, top drivers.
- Market metrics card: price metrics and expert-style indicators.
- Evidence panel: ranked articles and explanation factors.
- Risk panel: data gaps, low confidence, conflicting signals, stale sources.
- Snapshot controls: save current snapshot and view previous.

### Error State

- Invalid ticker: explain ticker was not found.
- No articles found: show market metrics and explain that sentiment signal is unavailable.
- API failure: show which provider failed and offer retry.
- Model failure: show raw data status and explain forecast is unavailable.

## 4. Interaction Patterns

- Ticker input supports submit by Enter and search button.
- Refresh button reruns ingestion and model pipeline.
- Article list supports filtering by sentiment, source, and date.
- Confidence and metric labels include tooltips.
- Forecast card should visually distinguish positive, negative, and neutral outlooks.
- Saved snapshot action should be disabled while analysis is still running.

## 5. Design System Direction

- Style: dense research dashboard, calm and analytical.
- Colors: neutral base with restrained green/red/yellow signal colors.
- Typography: readable sans-serif, tabular numerals for metrics.
- Components: cards for individual analytic modules, tables for article evidence, badges for sentiment and confidence.
- Icons: use standard icons for refresh, save, alert, external link, trend up, trend down, neutral signal, and info.

## 6. Accessibility

- All controls keyboard accessible.
- Forecast color must not be the only signal; include text labels and icons.
- Tables need column headers and meaningful empty states.
- Tooltips must have accessible labels.
- Loading states should announce progress changes where practical.

## 7. Technical Implementation Notes

- Keep dashboard state URL-addressable by ticker when possible.
- Separate ingestion, sentiment, forecast, and UI state.
- Cache article results by ticker and timestamp to avoid repeated provider calls.
- Store model version with every forecast.
- Preserve raw source links for auditability.
