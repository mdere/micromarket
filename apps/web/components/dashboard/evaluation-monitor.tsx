import type { EvaluationRefreshResponse, EvaluationSummaryResponse } from "@/lib/micromarket-types";
import { formatAccuracy, formatPercent } from "@/lib/format";

type EvaluationMonitorProps = {
  error: string | null;
  isLoading: boolean;
  isRefreshing: boolean;
  onRefresh: () => void;
  refreshResult: EvaluationRefreshResponse | null;
  summary: EvaluationSummaryResponse | null;
};

export function EvaluationMonitor({
  error,
  isLoading,
  isRefreshing,
  onRefresh,
  refreshResult,
  summary
}: EvaluationMonitorProps) {
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <h2>Evaluation Monitor</h2>
          <span>{summary?.evaluated_forecasts ?? 0} evaluated forecasts</span>
        </div>
        <button className="secondary-button" disabled={isRefreshing} type="button" onClick={onRefresh}>
          {isRefreshing ? "Refreshing" : "Refresh"}
        </button>
      </div>
      {error ? <p className="error-text">{error}</p> : null}
      {isLoading ? <p className="loading-text">Loading evaluation summary...</p> : null}
      {refreshResult ? (
        <p className="body-text">
          Refresh complete: {refreshResult.evaluated_forecasts} evaluated,{" "}
          {refreshResult.skipped_forecasts} skipped.
        </p>
      ) : null}
      {refreshResult?.errors.length ? (
        <div className="evaluation-errors">
          {refreshResult.errors.map((item) => (
            <p className="warning-text" key={item.forecast_run_id}>
              {item.message}
            </p>
          ))}
        </div>
      ) : null}
      {!isLoading && summary?.by_horizon.length ? (
        <div className="evaluation-grid">
          {summary.by_horizon.map((item) => (
            <article className="evaluation-row" key={item.horizon}>
              <strong>{item.horizon.replaceAll("_", " ")}</strong>
              <span>{item.evaluated_forecasts} forecasts</span>
              <span>{formatAccuracy(item.directional_accuracy)} accuracy</span>
              <span>{formatPercent(item.mean_absolute_error)} mean error</span>
              <span>{formatPercent(item.baseline_mean_absolute_error)} baseline error</span>
            </article>
          ))}
        </div>
      ) : !isLoading ? (
        <p className="muted-text">
          No evaluated forecasts yet. Run evaluation refresh after forecast horizons expire to
          populate model monitoring.
        </p>
      ) : null}
    </section>
  );
}
