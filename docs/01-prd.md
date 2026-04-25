# Product Requirements Document: micromarket

## 1. Introduction

micromarket is a web-based AI research assistant for stock analysis. It ingests recent company-related articles, analyzes sentiment and relevance, combines those signals with stock-market metrics, and presents an explainable forecast for likely price direction and percentage movement.

The product is intended to support investment research. It must not present output as guaranteed performance, individualized investment advice, or an automated trading instruction.

## 2. Goals and Objectives

- Help users quickly understand current news sentiment around a company.
- Estimate likely short-term stock movement using sentiment and market features.
- Show prediction confidence, forecast range, and supporting evidence.
- Provide relevant stock metrics in the same view as article sentiment.
- Let users save research snapshots for later comparison.

## 3. Target Users

### Primary Persona: Individual Research Investor

- Tracks public companies before deciding whether to buy, sell, or hold.
- Reads financial news but wants faster signal extraction.
- Needs transparent evidence and risk notes.
- May not have institutional tooling.

### Secondary Persona: AIML Builder/Researcher

- Wants to experiment with sentiment and market prediction models.
- Needs data ingestion, model outputs, and evaluation metrics.
- Values explainability and reproducibility.

## 4. User Stories

- As an investor, I want to enter a ticker and see recent article sentiment so I can understand current market narrative.
- As an investor, I want to see predicted price direction and percent movement so I can decide whether to research further.
- As an investor, I want to see why the model produced a signal so I can judge whether I trust it.
- As an investor, I want relevant market metrics next to sentiment so I do not rely on news alone.
- As a researcher, I want saved snapshots so I can evaluate prediction quality later.

## 5. Functional Requirements

### 5.1 Ticker Research

- User can enter a ticker symbol.
- System validates the ticker and displays company name, exchange, sector, and latest available price.
- System handles invalid, delisted, unsupported, or ambiguous tickers.

### 5.2 Article Ingestion

- System retrieves recent articles for the selected company.
- System stores article title, source, URL, publication date, summary, and retrieved timestamp.
- System detects likely duplicates or syndication overlap.
- System assigns a company relevance score to avoid articles that mention the company only incidentally.

### 5.3 Sentiment Processing

- System classifies article sentiment as positive, neutral, or negative.
- System calculates a numeric sentiment score.
- System identifies important sentiment drivers such as earnings, product launches, layoffs, lawsuits, analyst upgrades, analyst downgrades, regulatory risk, macro conditions, or executive changes.
- System aggregates sentiment across articles with recency and relevance weighting.

### 5.4 Market Metrics

- System displays current price, daily change, volume, market cap, 52-week range, moving averages, volatility proxy, beta if available, P/E if available, and analyst consensus if available.
- System labels metrics unavailable from the selected provider rather than hiding gaps silently.

### 5.5 Forecasting

- System predicts price direction over a defined horizon.
- System predicts estimated percent movement or range.
- System displays confidence level and uncertainty.
- System explains the top factors contributing to the forecast.
- System records forecast timestamp for later evaluation.

### 5.6 Decision-Support Dashboard

- System summarizes bullish, bearish, and neutral signals.
- System shows article evidence linked to each signal.
- System flags high-risk conditions such as low source count, stale data, conflicting signals, or low model confidence.
- System avoids imperative investment instructions such as "buy now" or "sell immediately."

### 5.7 Research Snapshots

- User can save a snapshot for a ticker.
- Snapshot includes articles, sentiment aggregate, market metrics, forecast, model version, and timestamp.
- User can view prior snapshots for the same ticker.

## 6. Non-Functional Requirements

- Performance: dashboard loads within 5 seconds for cached data and 15 seconds for fresh ingestion in MVP.
- Reliability: ingestion failures must be visible and recoverable.
- Explainability: every prediction must expose major input factors.
- Security: API keys must never be exposed in frontend code.
- Privacy: user watchlists and snapshots should be private by default.
- Accessibility: target WCAG 2.1 AA for core views.
- Compliance: include clear financial-risk disclaimers and avoid personalized financial advice claims.
- Observability: log ingestion failures, model errors, latency, and prediction records.

## 7. Design Considerations

- Interface should feel like a research terminal, not a marketing landing page.
- Prioritize dense, scannable information.
- Use clear status indicators for data freshness, confidence, and source quality.
- Separate "model output" from "source evidence" visually.
- Forecast should be a range with uncertainty, not a single overconfident number.

## 8. Success Metrics

- 80% of pilot users can complete a ticker research flow without help.
- Dashboard produces a traceable sentiment summary for at least 90% of valid ticker searches with available articles.
- Forecast records include complete input lineage for 100% of successful predictions.
- Pilot users rate evidence transparency at 4 out of 5 or higher.
- Model baseline beats a naive no-change baseline for selected evaluation windows before expanding the product.

## 9. Open Questions

- Initial prediction horizon: next close, 3 trading days, 7 trading days, or 30 days?
- Initial data providers for articles and market data?
- Initial modeling strategy: classical ML baseline, fine-tuned language model features, or ensemble?
- Will authentication be included in MVP or deferred?
- How much historical data is available for backtesting?
