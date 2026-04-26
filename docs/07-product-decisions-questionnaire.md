# micromarket Product Decisions Questionnaire

Fill this in directly. Short answers are fine. If you are unsure, write your current preference and any concerns.

After you complete it, I can assess the answers and turn them into the technical architecture, data/model strategy, and first implementation roadmap.

## 1. Product Scope

### 1.1 What market should v1 support?

Examples: US equities only, US equities + ETFs, global stocks, crypto, forex.

Answer: For now lets support US equities + ETFs - since I do invest in S&P500 too.

### 1.2 Should v1 support one ticker at a time or a watchlist?

Recommendation for MVP: one ticker at a time.

Answer: Yeah one ticker for sure, but I do want tdo think about the architecture to make sure we can scale it with out huge refactors.

### 1.3 Is this for personal use first, or should it become a multi-user SaaS?

This affects authentication, database design, deployment, privacy, and compliance work.

Answer: No this is personal use. I plan to run this on my home server or use some AWS cloud resources. Like S3 buckets maybe or store it on network drives.

### 1.4 Which user should the MVP serve first?

Examples: you as the first user, individual investors, active traders, AIML researchers, financial analysts.

Answer: So I want to focus on the AIML rersearcher and financial analysts. The reason I think we need to focus on that first is that this whole system's foundation is based on data. Then when we feel that we have a good data pipeline and API endpoints we then can build a UI ontop of it for the indiviual investors and active traders

## 2. Prediction Goal

### 2.1 What prediction horizon matters most?

Options: next close, 3 trading days, 7 trading days, 30 days.

Answer: I am uncertain how to apprroach this. obviously next close will need to be super accurate. An the more we forecast ahead, obviously its a prediction. I think as long we have a way to track confidence level on each tier based on sentiment maybe a feature would implement.

### 2.2 What should the model predict first?

Options: direction only, percent change, price range, confidence score, or a combination.

Answer: I would say combination. I think % and confidence score is a priority. Price range is not really a huge priority right now - I think I just want to focus on whether based on sentiments of articles gives us confidence to whether trust to invest.

### 2.3 What would count as good enough for the MVP?

Examples: faster research workflow, understandable sentiment summary, better than naive baseline, useful confidence flags.

Answer: Not entirely sure which would be the best apprroach. Maybe needd to assess pros and cons. I think all of them are good - faster research workflow not so much as we can always scale. But understandable sentiment summary, better than naive baseline, useful confidence flags seems like it is a necessary requirement to make sure our models are going in the right direction.

### 2.4 Should the forecast be framed as bullish/bearish/neutral, or avoid those labels?

This affects UX language and compliance posture.

Answer: I think this will be the next version.

## 3. Data Sources

### 3.1 What article sources should v1 use?

Examples: RSS feeds, NewsAPI, Alpha Vantage news, Finnhub news, SEC filings, user-pasted URLs, manually uploaded text.

Answer: I would say manually uploaded text first, then user-pasted URLSs as this will be entry point to web scraping, then APIs

### 3.2 Are paid APIs acceptable, or free/open sources only for now?

Answer: I woul say free/open sources only for now. I would like to consider paid as a plugin - like turn it on for a month at a time and turn it off.

### 3.3 Should users be able to paste article URLs manually?

This is useful if automated news search is weak or expensive.

Answer: Yes absolutely this is MVP feature

### 3.4 What market data source should v1 use?

Examples: yfinance, Alpha Vantage, Polygon, Finnhub, IEX Cloud, Nasdaq Data Link.

Answer: I am not farmiliar which one is the best use case for our MVP.

### 3.5 How fresh does the data need to be?

Examples: real-time, delayed intraday, daily close is enough, manual refresh is enough.

Answer: Does not need to be real-time for MVP - I would like to treat MVP as an entry point for me to research quickly to make decisions if I should invest or not.

## 4. Model Strategy

### 4.1 Do you want a simple baseline model first?

Recommendation: yes. Start with a baseline so future models can be measured honestly.

Answer: I agree to start on a baseline - but mechanisms to measure for improvements and ways for us to track retrospectives.

### 4.2 Should sentiment use an LLM/API, a local model, or both?

Examples: OpenAI API, Hugging Face local model, FinBERT, custom model trained later.

Answer: I want the system to be specifically hosted at home server - but since I dont' have a beefy CUDA Nvidia GPU yet, we may need to rely on OpenAI API or something to help us generate the model.

### 4.3 Should the model explain its reasoning in plain English?

Recommendation: yes, but every explanation should link back to evidence and avoid unsupported claims.

Answer: Yes I agree with recommendation

### 4.4 Should forecasts be stored for later accuracy evaluation?

Recommendation: yes. Store every forecast with timestamp, ticker, horizon, model version, inputs, and later actual outcome.

Answer: Yes I agree with recommendation.

### 4.5 What matters more in the first model: accuracy, explainability, speed, or low cost?

Answer:  Accuracy then explainability

## 5. User Experience

### 5.1 What should the main dashboard prioritize?

Options: forecast, sentiment, article evidence, market metrics, risk warnings, historical snapshots.

Answer: Forecast for sure - then backed with sentiment and article evidence. everything else could be post MVP

### 5.2 Should the app ever say buy, sell, or hold?

Recommendation: avoid direct instructions in MVP. Use decision-support language instead.

Answer: I agree with REcommendation. This tool is to provide MVP analyst to give confidence whether to invest or rnot

### 5.3 What disclaimers or guardrails do you want?

Examples: not financial advice, educational/research use only, predictions can be wrong, verify independently.

Answer: MVP should support research to provide some level of confidence with based evidence to invest or not.

### 5.4 How much raw evidence should users see?

Examples: summaries only, ranked article list, full extracted article text, sentiment drivers with source links.

Answer: I would like to see an accurate summary - but it should also list out the amount of evidence found to back the forecast. Like if there is one evidence saying with high sentiment, I wouln't trust it until I see multiple articles with close enough sentiment to back each other.

### 5.5 Should the interface feel more like a financial terminal, a clean SaaS dashboard, or a research notebook?

Answer: So I intend to have my family members use this. It needs to be easy to use.

## 6. Technical Preferences

### 6.1 Preferred frontend stack?

Examples: Next.js, React + Vite, plain HTML, Streamlit, Dash.

Answer: I am leaning towards to server side rendering like framework. Reason being to limit the amount of friction of API integration. I do want an architecture where I have multiple microservices like golang running in the backend and the nextJS server side is an orchestrator. 

### 6.2 Preferred backend stack?

Examples: FastAPI, Flask, Django, Node/Express, no separate backend for MVP.

Answer: So I am uncertain - I feel I should do Python, but I've always leaned towards golang. What would you recommend? I take it python should be more focused on data pipeline and building models. And golang micro layer as an API layer and MLAAS (Machine Learning as a Service or Agent service) and Server side Rendering UI Client to serve as an orchestror and client rerndering.

Please provide pros and cons?

### 6.3 Preferred database?

Examples: SQLite, PostgreSQL, DuckDB, local files, Supabase.

Answer: postgreSQL is fine for the backend services and general data. But models probably locally on the server assuming I have drive space and using S3 AWS cloud as an archive.

### 6.4 Local-only first or hosted from day one?

Answer: Local only first

### 6.5 Do you want this structured as a single app or separate frontend/backend projects?

Answer: I believe I answered above in 6.2

## 7. MVP Constraints

### 7.1 How much time do you want to spend on v1?

Examples: weekend prototype, 1 week, 2-4 weeks, 2-3 months.

Answer: realistically 2-3 months

### 7.2 Are you building this alone?

Answer: For now yes.

### 7.3 What matters most for v1?

Options: speed, accuracy, explainability, polish, low cost, extensibility.

Answer: Accuracy and explainability - then polish then extensibility then low-cost

### 7.4 Are there tools, APIs, frameworks, or cloud services you want to avoid?

Answer: Any frameworks that haven't been maintainedd. I do want to avoid paid cloud services for now. 

## 8. Compliance and Risk

### 8.1 Should the product be strictly research-only?

Answer: For the most part yes.

### 8.2 Should user-specific financial context be excluded from v1?

Examples: income, risk tolerance, holdings, net worth, personal investment goals.

Answer: No - not for MVP

### 8.3 Should the app log or display model limitations every time it produces a forecast?

Answer: Yes.

## 9. Notes / Extra Context

Add anything else I should know before turning this into architecture and build tasks.

Answer:  I think the biggest thing is to provide pros and cons and multiple different architecturers that can solve the solution and we can pick from there.
