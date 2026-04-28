import type { ForecastRunResponse } from "@/lib/micromarket-types";
import { directionClass, formatPercent, formatScore } from "@/lib/format";

export function ForecastPanel({ forecast }: { forecast: ForecastRunResponse | null }) {
  return (
    <section className="panel primary-panel">
      <div className="section-heading">
        <h1>Selected Forecast</h1>
        <span>{forecast?.horizon ?? "No forecast"}</span>
      </div>
      {forecast ? (
        <div className="forecast-layout">
          <div>
            <div className={`direction ${directionClass(forecast.predicted_direction)}`}>
              {forecast.predicted_direction}
            </div>
            <p className="muted-text">
              {formatPercent(forecast.predicted_percent_change)} projected movement, confidence{" "}
              {formatScore(forecast.confidence_score)}
            </p>
          </div>
          <div className="factor-list">
            {forecast.top_factors.map((factor) => (
              <span key={factor}>{factor}</span>
            ))}
          </div>
        </div>
      ) : (
        <p className="muted-text">Run or select an analysis to view forecast output.</p>
      )}
    </section>
  );
}
