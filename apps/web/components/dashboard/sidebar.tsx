import { FormEvent } from "react";

type SidebarProps = {
  articleUrl: string;
  analysisError: string | null;
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
  tickerOptions: string[];
};

export function DashboardSidebar({
  articleUrl,
  analysisError,
  isSubmitting,
  manualText,
  onAnalysisSubmit,
  onArticleUrlChange,
  onManualTextChange,
  onTickerChange,
  onTickerSelect,
  onWorkspaceSubmit,
  selectedTicker,
  tickerInput,
  tickerOptions
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

      {tickerOptions.length ? (
        <section className="ticker-list" aria-label="recent tickers">
          <h2>Recent Tickers</h2>
          <div>
            {tickerOptions.map((ticker) => (
              <button
                className={ticker === selectedTicker ? "ticker-pill active" : "ticker-pill"}
                key={ticker}
                type="button"
                onClick={() => onTickerSelect(ticker)}
              >
                {ticker}
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
