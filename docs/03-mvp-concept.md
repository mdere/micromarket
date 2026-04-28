# MVP Concept: micromarket

## 1. Core MVP Hypothesis

Individual research investors will find value in a single-ticker dashboard that combines recent article sentiment, relevant stock metrics, and an explainable short-term forecast, provided that the output is transparent enough to support independent decision-making.

## 2. Target Audience

The first MVP targets individual investors who already track specific US public equities and want faster article-driven research before deciding whether to buy, sell, hold, or continue investigating.

## 3. Problem Solved

Investors have to manually read many articles, judge sentiment, compare market metrics, and estimate whether the market narrative may affect price. This is slow, inconsistent, and hard to audit later.

## 4. Minimum Feature Set

### In Scope

- Single ticker search.
- Company profile and latest basic price metrics.
- Article ingestion for the selected ticker.
- Article relevance and duplicate handling at a basic level.
- Sentiment classification and aggregate sentiment score.
- Forecast direction and percent movement range for one defined horizon.
- Confidence score and risk flags.
- Evidence panel showing articles and top sentiment drivers.
- Ticker-centered analysis history for repeated research runs.
- Save research snapshot.
- Basic snapshot history for the selected ticker.
- Clear financial-risk disclaimer.

### Out of Scope

- Automated trading.
- Personalized portfolio advice.
- Multi-ticker portfolio optimization.
- Watchlist or batch analysis workflows.
- Real-time streaming news.
- Paid broker integration.
- Options, crypto, forex, or non-US markets.
- Social media sentiment.
- Mobile-native app.
- Complex backtesting UI.
- User collaboration and sharing.

## 5. Key Constraints

- Keep MVP narrow enough for one developer/researcher to build.
- Use free or low-cost data providers initially.
- Make all model outputs auditable.
- Avoid regulated-advice language.
- Establish a baseline model before using more complex approaches.

## 6. Initial Success Metrics

- 10 pilot ticker analyses completed successfully.
- At least 90% of successful forecasts include evidence links and model version.
- At least 80% of pilot users understand why the system produced a bullish, bearish, or neutral signal.
- Directional forecast can be evaluated against real market outcomes for the chosen horizon.
- User feedback identifies whether the dashboard improves research speed compared with manual reading.
