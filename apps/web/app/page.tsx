"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ArticleHistory } from "@/components/dashboard/article-history";
import { DashboardNotices } from "@/components/dashboard/notices";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { EvaluationMonitor } from "@/components/dashboard/evaluation-monitor";
import { EvidencePanel } from "@/components/dashboard/evidence-panel";
import { ForecastPanel } from "@/components/dashboard/forecast-panel";
import { Metric } from "@/components/dashboard/metric";
import { RelatedSignalsPanel } from "@/components/dashboard/related-signals-panel";
import { RelatedWorkspacesPanel } from "@/components/dashboard/related-workspaces-panel";
import { SentimentMarketGrid } from "@/components/dashboard/sentiment-market-grid";
import { TimelinePanel } from "@/components/dashboard/timeline-panel";
import { formatPrice, normalizeTicker } from "@/lib/format";
import type {
  AnalysisResponse,
  AssetWorkspaceResponse,
  ArticleHistoryItem,
  EvaluationRefreshResponse,
  EvaluationSummaryResponse,
  RelatedWorkspaceResponse,
  TrackingNeedResponse
} from "@/lib/micromarket-types";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [tickerInput, setTickerInput] = useState("SPY");
  const [selectedTicker, setSelectedTicker] = useState("SPY");
  const [manualText, setManualText] = useState("");
  const [articleUrl, setArticleUrl] = useState("");
  const [activeAnalysis, setActiveAnalysis] = useState<AnalysisResponse | null>(null);
  const [tickerAnalyses, setTickerAnalyses] = useState<AnalysisResponse[]>([]);
  const [assetWorkspaces, setAssetWorkspaces] = useState<AssetWorkspaceResponse[]>([]);
  const [relatedWorkspaces, setRelatedWorkspaces] = useState<RelatedWorkspaceResponse[]>([]);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisResponse[]>([]);
  const [evaluationSummary, setEvaluationSummary] = useState<EvaluationSummaryResponse | null>(
    null
  );
  const [evaluationRefresh, setEvaluationRefresh] = useState<EvaluationRefreshResponse | null>(
    null
  );
  const [statusMessage, setStatusMessage] = useState("Ready");
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);
  const [isLoadingRelatedWorkspaces, setIsLoadingRelatedWorkspaces] = useState(false);
  const [isLoadingEvaluation, setIsLoadingEvaluation] = useState(false);
  const [isRefreshingEvaluation, setIsRefreshingEvaluation] = useState(false);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);

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

  const articleHistory = useMemo<ArticleHistoryItem[]>(() => {
    const articles = new Map<string, ArticleHistoryItem>();
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

  async function loadAssetWorkspaces(query?: string) {
    try {
      const suffix = query ? `?query=${encodeURIComponent(query)}` : "";
      const response = await fetch(`${apiBaseUrl}/assets${suffix}`, { cache: "no-store" });
      if (!response.ok) {
        setWorkspaceError(`Workspaces unavailable (${response.status}).`);
        return;
      }
      setAssetWorkspaces((await response.json()) as AssetWorkspaceResponse[]);
    } catch {
      setWorkspaceError("API not reachable while loading workspaces.");
    }
  }

  async function onboardAssetWorkspace(symbol: string) {
    const response = await fetch(`${apiBaseUrl}/assets/onboard`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol })
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail ?? `Workspace onboarding failed (${response.status}).`);
    }
    return body as AssetWorkspaceResponse;
  }

  async function loadEvaluationSummary() {
    setEvaluationError(null);
    setIsLoadingEvaluation(true);
    try {
      const response = await fetch(`${apiBaseUrl}/evaluations/summary`, { cache: "no-store" });
      if (!response.ok) {
        setEvaluationError(`Evaluation summary unavailable (${response.status}).`);
        return;
      }
      setEvaluationSummary((await response.json()) as EvaluationSummaryResponse);
    } catch {
      setEvaluationError("API not reachable while loading evaluation summary.");
    } finally {
      setIsLoadingEvaluation(false);
    }
  }

  async function refreshEvaluations() {
    setEvaluationError(null);
    setEvaluationRefresh(null);
    setIsRefreshingEvaluation(true);
    setStatusMessage("Refreshing evaluations");
    try {
      const response = await fetch(`${apiBaseUrl}/evaluations/refresh`, {
        method: "POST",
        cache: "no-store"
      });
      const body = await response.json();
      if (!response.ok) {
        setEvaluationError(body.detail ?? `Evaluation refresh failed (${response.status}).`);
        return;
      }
      setEvaluationRefresh(body as EvaluationRefreshResponse);
      setStatusMessage("Evaluation refresh completed");
      await loadEvaluationSummary();
    } catch {
      setEvaluationError("API not reachable while refreshing evaluations.");
    } finally {
      setIsRefreshingEvaluation(false);
    }
  }

  async function loadTickerWorkspace(symbol: string, preferredAnalysisId?: string) {
    const normalized = normalizeTicker(symbol);
    if (!normalized) {
      setStatusMessage("Enter a ticker to load its workspace.");
      return;
    }

    setWorkspaceError(null);
    setIsLoadingWorkspace(true);
    setIsLoadingRelatedWorkspaces(true);
    setSelectedTicker(normalized);
    setTickerInput(normalized);
    setStatusMessage(`Loading ${normalized} history`);
    try {
      try {
        await onboardAssetWorkspace(normalized);
        await loadAssetWorkspaces();
      } catch (error) {
        setWorkspaceError(
          error instanceof Error ? error.message : `${normalized} workspace onboarding failed.`
        );
      }
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
      await loadRelatedWorkspaces(normalized);
      setStatusMessage(
        analyses.length ? `${normalized} history loaded` : `${normalized} workspace ready`
      );
    } catch {
      setWorkspaceError("API not reachable while loading ticker history.");
    } finally {
      setIsLoadingWorkspace(false);
      setIsLoadingRelatedWorkspaces(false);
    }
  }

  async function loadRelatedWorkspaces(symbol: string) {
    const response = await fetch(`${apiBaseUrl}/analyses/related-workspaces?ticker=${symbol}`, {
      cache: "no-store"
    });
    if (!response.ok) {
      setWorkspaceError(`${symbol} related workspaces unavailable (${response.status}).`);
      setRelatedWorkspaces([]);
      return;
    }
    setRelatedWorkspaces((await response.json()) as RelatedWorkspaceResponse[]);
  }

  useEffect(() => {
    void loadRecentAnalyses();
    void loadAssetWorkspaces();
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
      await loadAssetWorkspaces();
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
    setSelectedAnalysisId(analysisId);
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
    } finally {
      setSelectedAnalysisId(null);
    }
  }

  async function updateTrackingNeedStatus(trackingNeedId: string, status: string) {
    setWorkspaceError(null);
    setStatusMessage(`Marking signal ${status}`);
    try {
      const response = await fetch(`${apiBaseUrl}/analyses/tracking-needs/${trackingNeedId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status })
      });
      const updated = (await response.json()) as TrackingNeedResponse | { detail?: string };
      if (!response.ok) {
        setWorkspaceError(
          "detail" in updated && updated.detail
            ? updated.detail
            : `Signal update failed (${response.status}).`
        );
        return;
      }
      setActiveAnalysis((current) =>
        current ? replaceTrackingNeed(current, updated as TrackingNeedResponse) : current
      );
      setTickerAnalyses((analyses) =>
        analyses.map((analysis) => replaceTrackingNeed(analysis, updated as TrackingNeedResponse))
      );
      if ((updated as TrackingNeedResponse).onboarding_status === "onboarded") {
        await loadAssetWorkspaces();
        await loadRelatedWorkspaces(selectedTicker);
      }
      setStatusMessage(`Signal marked ${status}`);
    } catch {
      setWorkspaceError("API not reachable while updating related signal.");
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
        <DashboardSidebar
          articleUrl={articleUrl}
          analysisError={analysisError}
          assetWorkspaces={assetWorkspaces}
          isSubmitting={isSubmitting}
          manualText={manualText}
          onAnalysisSubmit={handleAnalysisSubmit}
          onArticleUrlChange={setArticleUrl}
          onManualTextChange={setManualText}
          onTickerChange={(value) => {
            setTickerInput(value);
            void loadAssetWorkspaces(value);
          }}
          onTickerSelect={(ticker) => void loadTickerWorkspace(ticker)}
          onWorkspaceSubmit={handleWorkspaceSubmit}
          selectedTicker={selectedTicker}
          tickerInput={tickerInput}
        />

        <section className="main-panel">
          <DashboardNotices
            activeAnalysis={activeAnalysis}
            excludedEvidenceCount={excludedEvidenceCount}
            workspaceError={workspaceError}
          />

          <section className="summary-strip">
            <Metric label="Ticker" value={selectedTicker} />
            <Metric label="Runs" value={String(tickerAnalyses.length)} />
            <Metric label="Articles" value={String(articleHistory.length)} />
            <Metric label="Quote" value={formatPrice(activeAnalysis?.market_quote?.price)} />
          </section>

          <TimelinePanel
            activeAnalysisId={activeAnalysis?.id ?? null}
            analyses={tickerAnalyses}
            isLoading={isLoadingWorkspace}
            onSelectAnalysis={(analysisId) => void selectAnalysis(analysisId)}
            selectedAnalysisId={selectedAnalysisId}
            selectedTicker={selectedTicker}
          />

          <ForecastPanel forecast={primaryForecast} />

          <SentimentMarketGrid analysis={activeAnalysis} />

          <RelatedSignalsPanel
            onStatusChange={(trackingNeedId, status) =>
              void updateTrackingNeedStatus(trackingNeedId, status)
            }
            onTickerSelect={(ticker) => void loadTickerWorkspace(ticker)}
            trackingNeeds={activeAnalysis?.tracking_needs ?? []}
          />

          <RelatedWorkspacesPanel
            isLoading={isLoadingRelatedWorkspaces}
            onTickerSelect={(ticker) => void loadTickerWorkspace(ticker)}
            relatedWorkspaces={relatedWorkspaces}
            selectedTicker={selectedTicker}
          />

          <EvaluationMonitor
            error={evaluationError}
            isLoading={isLoadingEvaluation}
            isRefreshing={isRefreshingEvaluation}
            onRefresh={() => void refreshEvaluations()}
            refreshResult={evaluationRefresh}
            summary={evaluationSummary}
          />

          <EvidencePanel articles={activeAnalysis?.articles ?? []} />

          <ArticleHistory articleHistory={articleHistory} selectedTicker={selectedTicker} />

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

function replaceTrackingNeed(
  analysis: AnalysisResponse,
  updated: TrackingNeedResponse
): AnalysisResponse {
  const trackingNeeds = analysis.tracking_needs.map((need) =>
    need.id === updated.id ? updated : need
  );
  return { ...analysis, tracking_needs: trackingNeeds };
}
