# MVP Development Plan: micromarket

## 1. MVP Goal

Build a working single-ticker research dashboard that proves whether article sentiment plus market metrics can produce useful, explainable short-term stock outlooks.

## 2. Target Audience

Initial users are individual investors and AIML builders who can tolerate beta-quality tooling and provide detailed feedback.

## 3. Core Feature Set

### Build Now

- Ticker search and validation.
- Market-data fetch.
- Article ingestion.
- Sentiment scoring.
- Forecast pipeline.
- Explainability/evidence view.
- Snapshot persistence.
- Basic model evaluation logging.

### Defer

- Accounts and billing.
- Watchlists.
- Alerts.
- Advanced backtesting.
- Trading integration.
- Personalized recommendations.

## 4. Suggested Technology Stack

- Frontend: React or Next.js with TypeScript.
- Styling: Tailwind CSS or existing project design stack.
- Backend API: Python FastAPI for ingestion and model orchestration.
- Data processing: pandas, scikit-learn, deterministic baseline sentiment first, then optional local LLM or transformer providers when measurable.
- Local LLM runtime: Ollama can be added later behind a provider interface for sentiment experiments, but it should not be required for default MVP operation.
- Database: PostgreSQL for local structured MVP storage.
- Market data: start with yfinance or another low-cost provider, then replace with production-grade provider later.
- Article data: RSS/news API/user URL ingestion for MVP.
- Jobs: simple synchronous pipeline first; move to background jobs after MVP.

## 5. Development Phases

### Phase 1: Project Skeleton

- Create app structure.
- Define data models for company, article, sentiment result, forecast, and snapshot.
- Add environment variable handling for provider keys.

### Phase 2: Data Ingestion

- Implement ticker validation.
- Implement market metric fetch.
- Implement article fetch and normalization.
- Store raw article metadata.

### Phase 3: Sentiment and Forecasting

- Add article relevance score.
- Add analysis as-of time so historical articles are evaluated against market data available at the article date.
- Add curated sentiment fixtures and improve the baseline sentiment classifier.
- Add optional Ollama/local LLM sentiment provider only after the baseline has measurable fixtures.
- Aggregate ticker sentiment.
- Add baseline forecast model.
- Store confidence, horizon, and model version.

### Phase 4: Dashboard

- Build ticker search.
- Build company/market metrics panel.
- Build sentiment and forecast cards.
- Build article evidence table.
- Build snapshot save/history.

### Phase 5: Testing and Pilot

- Run functional, integration, and usability testing.
- Backtest a small set of stored forecasts.
- Collect pilot feedback.

## 6. Deployment Approach

- Local-first development.
- MVP can run as a local web app for personal testing.
- Pilot deployment can use a small cloud VM or managed app platform.
- Store secrets in environment variables, not source code.

## 7. Success Metrics

- Valid ticker dashboard completes in under 15 seconds for fresh analysis.
- Forecast records always include data timestamp and model version.
- At least 90% of article rows include source, URL, date, relevance, and sentiment.
- Users can identify top forecast drivers within 30 seconds.
- Baseline prediction performance is measured against naive benchmarks before broader launch.

## 8. Key Risks and Mitigations

- Risk: Article data quality is poor. Mitigation: source labels, relevance score, duplicate detection, and data-gap warnings.
- Risk: Forecast appears more certain than it is. Mitigation: ranges, confidence labels, and explicit uncertainty notes.
- Risk: Legal/compliance ambiguity. Mitigation: decision-support framing, disclaimers, no personalized recommendations.
- Risk: Model overfits small data. Mitigation: baseline comparisons, holdout evaluation, model versioning.
- Risk: Provider rate limits. Mitigation: caching and manual refresh limits.

## 9. Post-MVP Decision Criteria

- Expand if users find the evidence view useful and model outputs are evaluable.
- Iterate if users trust sentiment summaries but not forecasts.
- Pivot toward research summarization if forecasting quality is weak.
- Stop or re-scope if data availability or compliance constraints block useful output.
