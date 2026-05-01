import { FormEvent } from "react";

import type { AssetWorkspaceResponse } from "@/lib/micromarket-types";

type SidebarProps = {
  articleUrl: string;
  analysisError: string | null;
  assetWorkspaces: AssetWorkspaceResponse[];
  isSubmitting: boolean;
  manualText: string;
  onAnalysisSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onArticleUrlChange: (value: string) => void;
  onManualTextChange: (value: string) => void;
  onTickerChange: (value: string) => void;
  onTickerSelect: (ticker: string) => void;
  onWorkspaceSubmit: (event: FormEvent<HTMLFormElement>) => void;
  selectedTicker: string;
  tickerInput: string;
};

export function DashboardSidebar({
  articleUrl,
  analysisError,
  assetWorkspaces,
  isSubmitting,
  manualText,
  onAnalysisSubmit,
  onArticleUrlChange,
  onManualTextChange,
  onTickerChange,
  onTickerSelect,
  onWorkspaceSubmit,
  selectedTicker,
  tickerInput
}: SidebarProps) {
  return (
    <aside className="panel left-panel">
      <form className="ticker-form" onSubmit={onWorkspaceSubmit}>
        <label>
          <span>Ticker Workspace</span>
          <input
            value={tickerInput}
            onChange={(event) => onTickerChange(event.target.value.toUpperCase())}
            maxLength={16}
            placeholder="SPY"
          />
        </label>
        <button type="submit">Load</button>
      </form>

      {assetWorkspaces.length ? (
        <section className="ticker-list" aria-label="recent tickers">
          <h2>Workspaces</h2>
          <div>
            {assetWorkspaces.map((workspace) => (
              <button
                className={workspace.symbol === selectedTicker ? "ticker-pill active" : "ticker-pill"}
                key={workspace.id}
                type="button"
                onClick={() => onTickerSelect(workspace.symbol)}
                title={`${workspace.analysis_count} runs, ${workspace.onboarding_status}`}
              >
                {workspace.symbol}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <form className="analysis-form" onSubmit={onAnalysisSubmit}>
        <div className="form-heading">
          <h2>New {selectedTicker} Analysis</h2>
          <span>one run, preserved lineage</span>
        </div>
        <label>
          <span>Manual Article Text</span>
          <textarea
            value={manualText}
            onChange={(event) => onManualTextChange(event.target.value)}
            placeholder="Paste article text or analyst notes"
            rows={8}
          />
        </label>
        <label>
          <span>Article URL</span>
          <input
            value={articleUrl}
            onChange={(event) => onArticleUrlChange(event.target.value)}
            placeholder="https://..."
          />
        </label>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Running" : "Run Analysis"}
        </button>
        {analysisError ? <p className="error-text">{analysisError}</p> : null}
      </form>
    </aside>
  );
}
