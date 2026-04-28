import type { AnalysisResponse } from "@/lib/micromarket-types";
import { formatDateTime, formatScore } from "@/lib/format";

type TimelinePanelProps = {
  activeAnalysisId: string | null;
  analyses: AnalysisResponse[];
  onSelectAnalysis: (analysisId: string) => void;
  selectedTicker: string;
};

export function TimelinePanel({
  activeAnalysisId,
  analyses,
  onSelectAnalysis,
  selectedTicker
}: TimelinePanelProps) {
  return (
    <section className="panel timeline-panel">
      <div className="section-heading">
        <h1>{selectedTicker} Analysis Timeline</h1>
        <span>{analyses.length} runs</span>
      </div>
      {analyses.length ? (
        <div className="timeline-list">
          {analyses.map((analysis) => {
            const forecast =
              analysis.forecast_runs.find((run) => run.horizon === analysis.primary_horizon) ??
              analysis.forecast_runs[0] ??
              null;
            return (
              <button
                className={activeAnalysisId === analysis.id ? "timeline-row active" : "timeline-row"}
                key={analysis.id}
                type="button"
                onClick={() => onSelectAnalysis(analysis.id)}
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
  );
}
