import { ApiStatus } from "@/components/api-status";

const mockMetrics = [
  ["Price", "$184.32"],
  ["3D Horizon", "Primary"],
  ["Evidence", "3 articles"],
  ["Confidence", "Pending"]
];

const mockEvidence = [
  ["Manual article input", "First MVP input path for analyst-controlled evidence."],
  ["Pasted URL", "Second MVP path for URL extraction and normalized article storage."],
  ["Provider interface", "Market data starts with yfinance behind a replaceable boundary."]
];

export default function Home() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <strong>micromarket</strong>
          <span>Research-only sentiment and forecast workspace</span>
        </div>
        <form className="ticker-form">
          <input aria-label="Ticker symbol" placeholder="Ticker, e.g. AAPL or SPY" />
          <button type="button">Analyze</button>
        </form>
      </header>

      <section className="dashboard" aria-label="micromarket dashboard scaffold">
        <aside className="column">
          <div className="card">
            <h2>Asset</h2>
            <div className="metric-grid">
              {mockMetrics.map(([label, value]) => (
                <div className="metric" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3>API Status</h3>
            <ApiStatus />
          </div>
        </aside>

        <section className="column">
          <div className="card">
            <h2>Primary Forecast</h2>
            <div className="forecast-value">
              <strong>3 trading days</strong>
              <span>scaffold</span>
            </div>
            <div className="pill-row">
              <span className="pill positive">Evidence-backed output required</span>
              <span className="pill warning">No buy/sell/hold advice</span>
              <span className="pill">Model version stored</span>
            </div>
          </div>

          <div className="card">
            <h2>Sentiment Summary</h2>
            <p>
              Sentiment, evidence strength, source agreement, and confidence calibration will
              appear here after the backend pipeline is implemented.
            </p>
          </div>
        </section>

        <aside className="column">
          <div className="card">
            <h2>Evidence</h2>
            <div className="evidence-list">
              {mockEvidence.map(([title, detail]) => (
                <div className="evidence-item" key={title}>
                  <strong>{title}</strong>
                  <span>{detail}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <section className="card wide">
          <h2>Limitation</h2>
          <p className="disclaimer">
            micromarket is research-only decision support. It does not provide personalized
            financial advice, and every forecast must display model limitations, evidence, horizon,
            confidence, and model version before it is treated as useful.
          </p>
        </section>
      </section>
    </main>
  );
}
