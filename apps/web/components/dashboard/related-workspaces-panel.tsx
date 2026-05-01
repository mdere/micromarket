import type { RelatedWorkspaceResponse } from "@/lib/micromarket-types";

type RelatedWorkspacesPanelProps = {
  isLoading: boolean;
  onTickerSelect: (ticker: string) => void;
  relatedWorkspaces: RelatedWorkspaceResponse[];
  selectedTicker: string;
};

export function RelatedWorkspacesPanel({
  isLoading,
  onTickerSelect,
  relatedWorkspaces,
  selectedTicker
}: RelatedWorkspacesPanelProps) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>Tracked Related Workspaces</h2>
        <span>{relatedWorkspaces.length} tickers</span>
      </div>
      {isLoading ? (
        <p className="loading-text">Loading related workspaces...</p>
      ) : relatedWorkspaces.length ? (
        <div className="related-workspace-list">
          {relatedWorkspaces.map((workspace) => (
            <article className="related-workspace-row" key={workspace.related_asset_id}>
              <div className="related-workspace-main">
                <button
                  className="related-signal-symbol"
                  type="button"
                  onClick={() => onTickerSelect(workspace.symbol)}
                >
                  {workspace.symbol}
                </button>
                <div>
                  <strong>{workspace.name ?? workspace.symbol}</strong>
                  <p>
                    {workspace.relationship_types.join(", ").replace(/_/g, " ")} from{" "}
                    {workspace.mention_count} accepted signal
                    {workspace.mention_count === 1 ? "" : "s"}
                  </p>
                </div>
              </div>
              <div className="evidence-meta">
                <span>{workspace.latest_status}</span>
                <span>priority {workspace.priority_score}</span>
                <span>{workspace.source_analysis_ids.length} source runs</span>
              </div>
              {workspace.evidence_snippets[0] ? (
                <p className="related-signal-evidence">{workspace.evidence_snippets[0]}</p>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-text">
          No accepted related workspaces for {selectedTicker}. Accept a ticker-backed related signal
          to keep it here.
        </p>
      )}
    </section>
  );
}
