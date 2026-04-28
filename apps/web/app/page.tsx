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
  created_at: string;
  completed_at: string | null;
  message: string;
  limitations: string[];
  articles: ArticleResponse[];
  market_quote: MarketQuoteResponse | null;
  sentiment_aggregate: SentimentAggregateResponse | null;
  forecast_runs: ForecastRunResponse[];
};

type EvaluationHorizonSummary = {
  horizon: string;
  evaluated_forecasts: number;
  directional_accuracy: string | null;
  mean_absolute_error: string | null;
  baseline_mean_absolute_error: string | null;
};

type EvaluationSummaryResponse = {
  evaluated_forecasts: number;
  by_horizon: EvaluationHorizonSummary[];
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [tickerInput, setTickerInput] = useState("SPY");
  const [selectedTicker, setSelectedTicker] = useState("SPY");
  const [manualText, setManualText] = useState("");
  const [articleUrl, setArticleUrl] = useState("");
  const [activeAnalysis, setActiveAnalysis] = useState<AnalysisResponse | null>(null);
  const [tickerAnalyses, setTickerAnalyses] = useState<AnalysisResponse[]>([]);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisResponse[]>([]);
  const [evaluationSummary, setEvaluationSummary] = useState<EvaluationSummaryResponse | null>(
    null
  );
  const [statusMessage, setStatusMessage] = useState("Ready");
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
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

  const tickerOptions = useMemo(() => {
    const seen = new Set<string>();
    return recentAnalyses
      .map((analysis) => analysis.ticker)
      .filter((ticker) => {
        if (seen.has(ticker)) {
          return false;
        }
        seen.add(ticker);
        return true;
      });
  }, [recentAnalyses]);

  const articleHistory = useMemo(() => {
    const articles = new Map<string, { article: ArticleResponse; analyses: string[] }>();
    for (const analysis of tickerAnalyses) {
      for (const article of analysis.articles) {
        const key = article.content_hash || article.id;
        const existing = articles.get(key);
        if (existing) {
          existing.analyses.push(analysis.id);
        } else {
          articles.set(key, { article, analyses: [analysis.id] });
        }
      }
    }
    return Array.from(articles.values());
  }, [tickerAnalyses]);

  const excludedEvidenceCount = useMemo(() => {
    return activeAnalysis?.articles.filter((article) => !article.included_in_forecast).length ?? 0;
  }, [activeAnalysis]);

  async function loadRecentAnalyses() {
    try {
      const response = await fetch(`${apiBaseUrl}/analyses`, { cache: "no-store" });
      if (!response.ok) {
        setWorkspaceError(`Recent analyses unavailable (${response.status}).`);
        return;
      }
      setRecentAnalyses((await response.json()) as AnalysisResponse[]);
    } catch {
      setWorkspaceError("API not reachable while loading recent analyses.");
    }
  }

  async function loadEvaluationSummary() {
    setEvaluationError(null);
    try {
      const response = await fetch(`${apiBaseUrl}/evaluations/summary`, { cache: "no-store" });
      if (!response.ok) {
        setEvaluationError(`Evaluation summary unavailable (${response.status}).`);
        return;
      }
      setEvaluationSummary((await response.json()) as EvaluationSummaryResponse);
    } catch {
      setEvaluationError("API not reachable while loading evaluation summary.");
    }
  }

  async function loadTickerWorkspace(symbol: string, preferredAnalysisId?: string) {
    const normalized = normalizeTicker(symbol);
    if (!normalized) {
      setStatusMessage("Enter a ticker to load its workspace.");
      return;
    }

    setWorkspaceError(null);
    setSelectedTicker(normalized);
    setTickerInput(normalized);
    setStatusMessage(`Loading ${normalized} history`);
    try {
      const response = await fetch(`${apiBaseUrl}/analyses?ticker=${normalized}`, {
        cache: "no-store"
      });
      if (!response.ok) {
        setWorkspaceError(`${normalized} history unavailable (${response.status}).`);
        return;
      }
      const analyses = (await response.json()) as AnalysisResponse[];
      setTickerAnalyses(analyses);
      const preferred = analyses.find((analysis) => analysis.id === preferredAnalysisId);
      setActiveAnalysis(preferred ?? analyses[0] ?? null);
      setStatusMessage(
        analyses.length ? `${normalized} history loaded` : `${normalized} workspace ready`
      );
    } catch {
      setWorkspaceError("API not reachable while loading ticker history.");
    }
  }

  useEffect(() => {
    void loadRecentAnalyses();
    void loadTickerWorkspace(selectedTicker);
    void loadEvaluationSummary();
  }, []);

  async function handleWorkspaceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadTickerWorkspace(tickerInput);
  }

  async function handleAnalysisSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ticker = normalizeTicker(tickerInput || selectedTicker);
    const articles = [];
    if (manualText.trim()) {
      articles.push({
        title: `${ticker} manual note`,
        source: "manual note",
        text: manualText.trim()
      });
    }
    if (articleUrl.trim()) {
      articles.push({ url: articleUrl.trim() });
    }
    if (!ticker) {
      setAnalysisError("Enter a ticker before running an analysis.");
      return;
    }
    if (articles.length === 0) {
      setAnalysisError("Add manual text or a URL before running an analysis.");
      return;
    }

    setAnalysisError(null);
    setIsSubmitting(true);
    setStatusMessage(`Running ${ticker} analysis`);
    try {
      const response = await fetch(`${apiBaseUrl}/analyses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          articles
        })
      });
      const body = await response.json();
      if (!response.ok) {
        setAnalysisError(body.detail ?? `Analysis failed (${response.status}).`);
        await loadTickerWorkspace(ticker);
        return;
      }
      const analysis = body as AnalysisResponse;
      setManualText("");
      setArticleUrl("");
      setStatusMessage("Analysis completed");
      await loadRecentAnalyses();
      await loadTickerWorkspace(analysis.ticker, analysis.id);
      await loadEvaluationSummary();
    } catch {
      setAnalysisError("API not reachable while running analysis.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function selectAnalysis(analysisId: string) {
    setWorkspaceError(null);
    setStatusMessage("Loading analysis");
    try {
      const response = await fetch(`${apiBaseUrl}/analyses/${analysisId}`, { cache: "no-store" });
      if (!response.ok) {
        setWorkspaceError(`Analysis unavailable (${response.status}).`);
        return;
      }
      setActiveAnalysis((await response.json()) as AnalysisResponse);
      setStatusMessage("Analysis loaded");
    } catch {
      setWorkspaceError("API not reachable while loading analysis.");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <strong>micromarket</strong>
          <span>Research-only ticker evidence workspace</span>
        </div>
        <div className="api-chip">{statusMessage}</div>
      </header>

      <section className="workspace" aria-label="micromarket research workspace">
        <aside className="panel left-panel">
          <form className="ticker-form" onSubmit={handleWorkspaceSubmit}>
            <label>
              <span>Ticker Workspace</span>
              <input
                value={tickerInput}
                onChange={(event) => setTickerInput(event.target.value.toUpperCase())}
                maxLength={16}
                placeholder="SPY"
              />
            </label>
            <button type="submit">Load</button>
          </form>

          {tickerOptions.length ? (
            <section className="ticker-list" aria-label="recent tickers">
              <h2>Recent Tickers</h2>
              <div>
                {tickerOptions.map((ticker) => (
                  <button
                    className={ticker === selectedTicker ? "ticker-pill active" : "ticker-pill"}
                    key={ticker}
                    type="button"
                    onClick={() => void loadTickerWorkspace(ticker)}
                  >
                    {ticker}
                  </button>
                ))}
              </div>
            </section>
          ) : null}

          <form className="analysis-form" onSubmit={handleAnalysisSubmit}>
            <div className="form-heading">
              <h2>New {selectedTicker} Analysis</h2>
              <span>one run, preserved lineage</span>
            </div>
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
            {analysisError ? <p className="error-text">{analysisError}</p> : null}
          </form>
        </aside>

        <section className="main-panel">
          {workspaceError ? (
            <section className="notice-panel error" aria-live="polite">
              {workspaceError}
            </section>
          ) : null}

          {activeAnalysis?.status === "failed" ? (
            <section className="notice-panel error" aria-live="polite">
              This analysis failed during processing. Its lineage is still visible, but forecast and
              sentiment outputs may be incomplete.
            </section>
          ) : null}

          {excludedEvidenceCount > 0 ? (
            <section className="notice-panel warning" aria-live="polite">
              {excludedEvidenceCount} article{excludedEvidenceCount === 1 ? "" : "s"} in the
              selected run {excludedEvidenceCount === 1 ? "was" : "were"} preserved for lineage but
              excluded from sentiment and forecast inputs.
            </section>
          ) : null}

          <section className="summary-strip">
            <Metric label="Ticker" value={selectedTicker} />
            <Metric label="Runs" value={String(tickerAnalyses.length)} />
            <Metric label="Articles" value={String(articleHistory.length)} />
            <Metric label="Quote" value={formatPrice(activeAnalysis?.market_quote?.price)} />
          </section>

          <section className="panel timeline-panel">
            <div className="section-heading">
              <h1>{selectedTicker} Analysis Timeline</h1>
              <span>{tickerAnalyses.length} runs</span>
            </div>
            {tickerAnalyses.length ? (
              <div className="timeline-list">
                {tickerAnalyses.map((analysis) => {
                  const forecast =
                    analysis.forecast_runs.find(
                      (run) => run.horizon === analysis.primary_horizon
                    ) ?? analysis.forecast_runs[0] ?? null;
                  return (
                    <button
                      className={
                        activeAnalysis?.id === analysis.id ? "timeline-row active" : "timeline-row"
                      }
                      key={analysis.id}
                      type="button"
                      onClick={() => void selectAnalysis(analysis.id)}
                    >
                      <span>{formatDateTime(analysis.created_at)}</span>
                      <strong>{forecast?.predicted_direction ?? analysis.status}</strong>
                      <em>{analysis.articles.length} articles</em>
                      <em>{formatScore(forecast?.confidence_score)} confidence</em>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="muted-text">
                No saved analyses for {selectedTicker}. Add article evidence to create the first run.
              </p>
            )}
          </section>

          <section className="panel primary-panel">
            <div className="section-heading">
              <h1>Selected Forecast</h1>
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
                    label="Included"
                    value={`${activeAnalysis.sentiment_aggregate.included_article_count}/${activeAnalysis.sentiment_aggregate.article_count}`}
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
              <h2>Evaluation Monitor</h2>
              <span>{evaluationSummary?.evaluated_forecasts ?? 0} evaluated forecasts</span>
            </div>
            {evaluationError ? <p className="error-text">{evaluationError}</p> : null}
            {evaluationSummary?.by_horizon.length ? (
              <div className="evaluation-grid">
                {evaluationSummary.by_horizon.map((summary) => (
                  <article className="evaluation-row" key={summary.horizon}>
                    <strong>{summary.horizon.replaceAll("_", " ")}</strong>
                    <span>{summary.evaluated_forecasts} forecasts</span>
                    <span>{formatAccuracy(summary.directional_accuracy)} accuracy</span>
                    <span>{formatPercent(summary.mean_absolute_error)} mean error</span>
                    <span>{formatPercent(summary.baseline_mean_absolute_error)} baseline error</span>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted-text">
                No evaluated forecasts yet. Run evaluation refresh after forecast horizons expire to
                populate model monitoring.
              </p>
            )}
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Selected Run Evidence</h2>
              <span>{activeAnalysis?.articles.length ?? 0} articles</span>
            </div>
            <EvidenceList articles={activeAnalysis?.articles ?? []} />
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>{selectedTicker} Article History</h2>
              <span>{articleHistory.length} unique articles</span>
            </div>
            {articleHistory.length ? (
              <div className="evidence-list">
                {articleHistory.map(({ article, analyses }) => (
                  <article className="evidence-row" key={article.content_hash}>
                    <div>
                      <ArticleTitle article={article} />
                      <p>{article.source ?? article.input_type}</p>
                    </div>
                    <div className="evidence-meta">
                      <span>{article.word_count} words</span>
                      <span>{analyses.length} run{analyses.length === 1 ? "" : "s"}</span>
                      <span className={article.included_in_forecast ? "included" : "excluded"}>
                        {article.included_in_forecast ? "included" : "excluded"}
                      </span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted-text">No article history for this ticker yet.</p>
            )}
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

function EvidenceList({ articles }: { articles: ArticleResponse[] }) {
  if (!articles.length) {
    return <p className="muted-text">No evidence loaded.</p>;
  }

  return (
    <div className="evidence-list">
      {articles.map((article) => (
        <article className="evidence-row" key={article.id}>
          <div>
            <ArticleTitle article={article} />
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
      ))}
    </div>
  );
}

function ArticleTitle({ article }: { article: ArticleResponse }) {
  const label = article.title ?? article.url ?? "Untitled article";

  if (!article.url) {
    return <strong>{label}</strong>;
  }

  return (
    <strong>
      <a href={article.url} rel="noreferrer" target="_blank">
        {label}
      </a>
    </strong>
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

function normalizeTicker(value: string) {
  return value.trim().toUpperCase();
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

function formatAccuracy(value?: string | null) {
  if (!value) {
    return "None";
  }
  return `${(Number(value) * 100).toFixed(0)}%`;
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

function formatDateTime(value?: string | null) {
  if (!value) {
    return "No timestamp";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
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
