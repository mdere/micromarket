import type { TrackingNeedResponse } from "@/lib/micromarket-types";

export function RelatedSignalsPanel({
  onStatusChange,
  onTickerSelect,
  trackingNeeds
}: {
  onStatusChange: (trackingNeedId: string, status: string) => void;
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
                  <span>{need.onboarding_status.replace(/_/g, " ")}</span>
                </div>
                <div className="related-signal-actions" aria-label={`Actions for ${need.name}`}>
                  <button
                    disabled={need.status === "accepted"}
                    type="button"
                    onClick={() => onStatusChange(need.id, "accepted")}
                  >
                    Accept
                  </button>
                  <button
                    disabled={need.status === "tracked"}
                    type="button"
                    onClick={() => onStatusChange(need.id, "tracked")}
                  >
                    Tracked
                  </button>
                  <button
                    disabled={need.status === "ignored"}
                    type="button"
                    onClick={() => onStatusChange(need.id, "ignored")}
                  >
                    Ignore
                  </button>
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
