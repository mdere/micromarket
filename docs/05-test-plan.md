# MVP Test Plan: micromarket

## 1. Objective

Verify that the micromarket MVP can ingest data for a ticker, generate sentiment and forecast outputs, display evidence transparently, and save research snapshots without presenting output as financial advice.

## 2. Scope

### In Scope

- Ticker search and validation.
- Market metrics retrieval.
- Article ingestion and normalization.
- Sentiment scoring and aggregation.
- Forecast generation.
- Confidence/risk display.
- Evidence article table.
- Snapshot save and retrieval.
- Basic accessibility and usability checks.
- Error handling for unavailable providers.

### Out of Scope

- Trading execution.
- Portfolio optimization.
- Billing and authentication.
- Mobile-native testing.
- Paid provider certification.
- Full regulatory review.

## 3. Features to Test

- Valid ticker returns company data.
- Invalid ticker returns a clear error.
- Market data failures do not crash the dashboard.
- Article ingestion stores source, URL, title, date, and retrieval time.
- Duplicate or low-relevance articles are labeled or filtered.
- Sentiment output includes class, score, and drivers.
- Forecast output includes direction, percent range, confidence, horizon, and model version.
- Evidence panel links forecast drivers back to article data.
- Snapshot captures all required analysis data.
- Prior snapshots can be viewed.

## 4. Testing Types

- Functional testing for each user flow.
- Integration testing across data providers, sentiment, forecast, and persistence.
- Regression testing for repeated ticker analyses.
- Usability testing with 3-5 pilot users.
- Accessibility smoke testing for keyboard navigation and color-independent signals.
- Performance testing for dashboard completion time.
- Security smoke testing for API key exposure and unsafe logs.

## 5. Test Environments

- Local development environment.
- Seed test tickers with known high-volume article coverage.
- Test data cases:
  - Common ticker with many articles.
  - Ticker with few articles.
  - Invalid ticker.
  - Article-provider failure.
  - Market-data-provider failure.

## 6. Entry Criteria

- MVP build deployed locally or to pilot environment.
- Required API keys configured.
- Database migrations or schema setup complete.
- At least five sample tickers identified.
- Basic smoke test passes for app startup.

## 7. Exit Criteria

- 100% of critical path test cases pass.
- No known critical or high defects remain open.
- Dashboard handles invalid and provider-failure states gracefully.
- Snapshot save/retrieve works for at least three tickers.
- Forecast records include model version and timestamp.
- Financial-disclaimer language appears in the MVP interface.

## 8. Risks and Contingencies

- Provider limits may block testing: use cached fixtures for repeatable tests.
- Model nondeterminism may affect expected outputs: validate structure and ranges, not exact language.
- Sparse article coverage may make forecast unusable: show low-confidence or unavailable states.
- Pilot users may interpret output as advice: test copy and labels carefully.

## 9. Test Deliverables

- Test case checklist.
- Bug list with severity.
- Test summary report.
- Pilot feedback notes.
- Model-evaluation summary for stored forecasts.
