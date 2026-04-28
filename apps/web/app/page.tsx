"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type ArticleResponse = {
  id: string;
  title: string | null;
  source: string | null;
  url: string | null;
  input_type: string;
  content_hash: string;
  word_count: number;
  raw_artifact_path: string | null;
  relevance_score: string | null;
  duplicate_group_id: string | null;
  included_in_forecast: boolean;
  exclusion_reason: string | null;
};

type MarketQuoteResponse = {
  provider: string;
  price: string | null;
  previous_close: string | null;
  volume: number | null;
  market_cap: number | null;
  quote_time: string | null;
  retrieved_at: string;
};

type SentimentAggregateResponse = {
  article_count: number;
  included_article_count: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  aggregate_score: string | null;
  agreement_score: string | null;
  evidence_strength_score: string | null;
  summary: string | null;
};

type ForecastRunResponse = {
  id: string;
  horizon: string;
  provider: string;
  model_name: string;
  model_version: string;
  predicted_direction: string;
  predicted_percent_change: string | null;
  confidence_score: string;
  baseline_direction: string | null;
  baseline_percent_change: string | null;
  top_factors: string[];
  limitations: string[];
  target_start_price: string | null;
  target_end_time: string | null;
};

type AnalysisResponse = {
  id: string;
  ticker: string;
  status: string;
  primary_horizon: string;
  input_mode: string;
  message: string;
  limitations: string[];
  articles: ArticleResponse[];
  market_quote: MarketQuoteResponse | null;
  sentiment_aggregate: SentimentAggregateResponse | null;
  forecast_runs: ForecastRunResponse[];
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [ticker, setTicker] = useState("SPY");
  const [manualText, setManualText] = useState("");
  const [articleUrl, setArticleUrl] = useState("");
  const [activeAnalysis, setActiveAnalysis] = useState<AnalysisResponse | null>(null);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisResponse[]>([]);
  const [statusMessage, setStatusMessage] = useState("Ready");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const primaryForecast = useMemo(() => {
    if (!activeAnalysis) {
      return null;
    }
    return (
      activeAnalysis.forecast_runs.find(
        (forecast) => forecast.horizon === activeAnalysis.primary_horizon
      ) ?? activeAnalysis.forecast_runs[0] ?? null
    );
  }, [activeAnalysis]);

  async function loadRecentAnalyses() {
    try {
      const response = await fetch(`${apiBaseUrl}/analyses`, { cache: "no-store" });
      if (!response.ok) {
        setStatusMessage(`Recent analyses unavailable (${response.status})`);
        return;
      }
      const analyses = (await response.json()) as AnalysisResponse[];
      setRecentAnalyses(analyses);
      if (!activeAnalysis && analyses.length > 0) {
        setActiveAnalysis(analyses[0]);
      }
    } catch {
      setStatusMessage("API not reachable");
    }
  }

  useEffect(() => {
    void loadRecentAnalyses();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const articles = [];
    if (manualText.trim()) {
      articles.push({
        title: `${ticker.toUpperCase()} manual note`,
        source: "manual note",
        text: manualText.trim()
      });
    }
    if (articleUrl.trim()) {
      articles.push({ url: articleUrl.trim() });
    }
    if (articles.length === 0) {
      setStatusMessage("Add manual text or a URL before running an analysis.");
      return;
    }

    setIsSubmitting(true);
    setStatusMessage("Running analysis");
    try {
      const response = await fetch(`${apiBaseUrl}/analyses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: ticker.trim().toUpperCase(),
          articles
        })
      });
      const body = await response.json();
      if (!response.ok) {
        setStatusMessage(body.detail ?? `Analysis failed (${response.status})`);
        return;
      }
      const analysis = body as AnalysisResponse;
      setActiveAnalysis(analysis);
      setStatusMessage("Analysis completed");
      await loadRecentAnalyses();
    } catch {
      setStatusMessage("API not reachable");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function selectAnalysis(analysisId: string) {
    setStatusMessage("Loading analysis");
    try {
      const response = await fetch(`${apiBaseUrl}/analyses/${analysisId}`, { cache: "no-store" });
      if (!response.ok) {
        setStatusMessage(`Analysis unavailable (${response.status})`);
        return;
      }
      setActiveAnalysis((await response.json()) as AnalysisResponse);
      setStatusMessage("Analysis loaded");
    } catch {
      setStatusMessage("API not reachable");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <strong>micromarket</strong>
          <span>Research-only market evidence workspace</span>
        </div>
        <div className="api-chip">{statusMessage}</div>
      </header>

      <section className="workspace" aria-label="micromarket research workspace">
        <aside className="panel left-panel">
          <form className="analysis-form" onSubmit={handleSubmit}>
            <label>
              <span>Ticker</span>
              <input
                value={ticker}
                onChange={(event) => setTicker(event.target.value)}
                maxLength={16}
                placeholder="SPY"
              />
            </label>
            <label>
              <span>Manual Article Text</span>
              <textarea
                value={manualText}
                onChange={(event) => setManualText(event.target.value)}
                placeholder="Paste article text or analyst notes"
                rows={8}
              />
            </label>
            <label>
              <span>Article URL</span>
              <input
                value={articleUrl}
                onChange={(event) => setArticleUrl(event.target.value)}
                placeholder="https://..."
              />
            </label>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Running" : "Run Analysis"}
            </button>
          </form>

          <section className="recent-list" aria-label="recent analyses">
            <h2>Recent Analyses</h2>
            {recentAnalyses.length === 0 ? (
              <p className="muted-text">No analyses loaded.</p>
            ) : (
              recentAnalyses.map((analysis) => (
                <button
                  className="recent-row"
                  key={analysis.id}
                  type="button"
                  onClick={() => void selectAnalysis(analysis.id)}
                >
                  <span>{analysis.ticker}</span>
                  <strong>{analysis.status}</strong>
                </button>
              ))
            )}
          </section>
        </aside>

        <section className="main-panel">
          <section className="summary-strip">
            <Metric label="Ticker" value={activeAnalysis?.ticker ?? "None"} />
            <Metric label="Input" value={formatInputMode(activeAnalysis?.input_mode)} />
            <Metric
              label="Quote"
              value={formatPrice(activeAnalysis?.market_quote?.price)}
            />
            <Metric
              label="Evidence"
              value={
                activeAnalysis?.sentiment_aggregate
                  ? `${activeAnalysis.sentiment_aggregate.included_article_count}/${activeAnalysis.sentiment_aggregate.article_count}`
                  : "0/0"
              }
            />
          </section>

          <section className="panel primary-panel">
            <div className="section-heading">
              <h1>Primary Forecast</h1>
              <span>{primaryForecast?.horizon ?? "No forecast"}</span>
            </div>
            {primaryForecast ? (
              <div className="forecast-layout">
                <div>
                  <div className={`direction ${directionClass(primaryForecast.predicted_direction)}`}>
                    {primaryForecast.predicted_direction}
                  </div>
                  <p className="muted-text">
                    {formatPercent(primaryForecast.predicted_percent_change)} projected movement,
                    confidence {formatScore(primaryForecast.confidence_score)}
                  </p>
                </div>
                <div className="factor-list">
                  {primaryForecast.top_factors.map((factor) => (
                    <span key={factor}>{factor}</span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="muted-text">Run or select an analysis to view forecast output.</p>
            )}
          </section>

          <section className="grid-two">
            <section className="panel">
              <div className="section-heading">
                <h2>Sentiment</h2>
                <span>{formatScore(activeAnalysis?.sentiment_aggregate?.aggregate_score)}</span>
              </div>
              <p className="body-text">
                {activeAnalysis?.sentiment_aggregate?.summary ?? "No sentiment summary loaded."}
              </p>
              {activeAnalysis?.sentiment_aggregate ? (
                <div className="compact-stats">
                  <Metric
                    label="Agreement"
                    value={formatScore(activeAnalysis.sentiment_aggregate.agreement_score)}
                  />
                  <Metric
                    label="Strength"
                    value={formatScore(activeAnalysis.sentiment_aggregate.evidence_strength_score)}
                  />
                </div>
              ) : null}
            </section>

            <section className="panel">
              <div className="section-heading">
                <h2>Market Quote</h2>
                <span>{activeAnalysis?.market_quote?.provider ?? "None"}</span>
              </div>
              <div className="compact-stats">
                <Metric label="Price" value={formatPrice(activeAnalysis?.market_quote?.price)} />
                <Metric
                  label="Prev Close"
                  value={formatPrice(activeAnalysis?.market_quote?.previous_close)}
                />
                <Metric label="Volume" value={formatNumber(activeAnalysis?.market_quote?.volume)} />
                <Metric
                  label="Market Cap"
                  value={formatNumber(activeAnalysis?.market_quote?.market_cap)}
                />
              </div>
            </section>
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Evidence</h2>
              <span>{activeAnalysis?.articles.length ?? 0} articles</span>
            </div>
            <div className="evidence-list">
              {activeAnalysis?.articles.length ? (
                activeAnalysis.articles.map((article) => (
                  <article className="evidence-row" key={article.id}>
                    <div>
                      <strong>{article.title ?? article.url ?? "Untitled article"}</strong>
                      <p>{article.source ?? article.input_type}</p>
                    </div>
                    <div className="evidence-meta">
                      <span>{article.word_count} words</span>
                      <span>relevance {formatScore(article.relevance_score)}</span>
                      <span className={article.included_in_forecast ? "included" : "excluded"}>
                        {article.included_in_forecast ? "included" : "excluded"}
                      </span>
                    </div>
                    {article.exclusion_reason ? (
                      <p className="warning-text">{article.exclusion_reason}</p>
                    ) : null}
                  </article>
                ))
              ) : (
                <p className="muted-text">No evidence loaded.</p>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Limitations</h2>
              <span>research only</span>
            </div>
            <ul className="limitations-list">
              {(activeAnalysis?.limitations.length
                ? activeAnalysis.limitations
                : ["Research-only output; not financial advice."]
              ).map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </section>
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatInputMode(value?: string) {
  if (!value) {
    return "None";
  }
  return value.replace("_", " ");
}

function formatPrice(value?: string | null) {
  if (!value) {
    return "None";
  }
  return `$${Number(value).toFixed(2)}`;
}

function formatPercent(value?: string | null) {
  if (!value) {
    return "None";
  }
  return `${Number(value).toFixed(2)}%`;
}

function formatScore(value?: string | null) {
  if (!value) {
    return "None";
  }
  return Number(value).toFixed(2);
}

function formatNumber(value?: number | null) {
  if (value === null || value === undefined) {
    return "None";
  }
  return Intl.NumberFormat("en-US", { notation: "compact" }).format(value);
}

function directionClass(direction: string) {
  if (direction === "up") {
    return "positive";
  }
  if (direction === "down") {
    return "negative";
  }
  return "neutral";
}
