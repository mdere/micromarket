import type { AnalysisResponse } from "@/lib/micromarket-types";
import { formatNumber, formatPrice, formatScore } from "@/lib/format";
import { Metric } from "./metric";

export function SentimentMarketGrid({ analysis }: { analysis: AnalysisResponse | null }) {
  return (
    <section className="grid-two">
      <section className="panel">
        <div className="section-heading">
          <h2>Sentiment</h2>
          <span>{formatScore(analysis?.sentiment_aggregate?.aggregate_score)}</span>
        </div>
        <p className="body-text">
          {analysis?.sentiment_aggregate?.summary ?? "No sentiment summary loaded."}
        </p>
        {analysis?.sentiment_aggregate ? (
          <div className="compact-stats">
            <Metric
              label="Included"
              value={`${analysis.sentiment_aggregate.included_article_count}/${analysis.sentiment_aggregate.article_count}`}
            />
            <Metric
              label="Strength"
              value={formatScore(analysis.sentiment_aggregate.evidence_strength_score)}
            />
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Market Quote</h2>
          <span>{analysis?.market_quote?.provider ?? "None"}</span>
        </div>
        <div className="compact-stats">
          <Metric label="Price" value={formatPrice(analysis?.market_quote?.price)} />
          <Metric label="Prev Close" value={formatPrice(analysis?.market_quote?.previous_close)} />
          <Metric label="Volume" value={formatNumber(analysis?.market_quote?.volume)} />
          <Metric label="Market Cap" value={formatNumber(analysis?.market_quote?.market_cap)} />
        </div>
      </section>
    </section>
  );
}
