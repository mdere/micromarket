import type { TrackingNeedResponse } from "@/lib/micromarket-types";

export function RelatedSignalsPanel({
  onTickerSelect,
  trackingNeeds
}: {
  onTickerSelect: (ticker: string) => void;
  trackingNeeds: TrackingNeedResponse[];
}) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>Related Signals</h2>
        <span>{trackingNeeds.length} suggestions</span>
      </div>
      {!trackingNeeds.length ? (
        <p className="muted-text">No related assets or themes detected for this run.</p>
      ) : (
        <div className="related-signal-list">
          {trackingNeeds.map((need) => {
            const symbol = need.suggested_symbol;
            return (
              <article className="related-signal-row" key={need.id}>
                <div className="related-signal-main">
                  {symbol ? (
                    <button
                      className="related-signal-symbol"
                      type="button"
                      onClick={() => onTickerSelect(symbol)}
                    >
                      {symbol}
                    </button>
                  ) : (
                    <strong>{need.name}</strong>
                  )}
                  <div>
                    <strong>{need.name}</strong>
                    <p>{need.reason}</p>
                  </div>
                </div>
                <div className="evidence-meta">
                  <span>{need.tracking_type.replace(/_/g, " ")}</span>
                  <span>priority {need.priority_score}</span>
                  <span>{need.status}</span>
                </div>
                {need.evidence_snippets[0] ? (
                  <p className="related-signal-evidence">{need.evidence_snippets[0]}</p>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
