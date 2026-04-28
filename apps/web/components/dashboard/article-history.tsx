import type { ArticleHistoryItem } from "@/lib/micromarket-types";
import { ArticleTitle } from "./evidence-list";

type ArticleHistoryProps = {
  articleHistory: ArticleHistoryItem[];
  selectedTicker: string;
};

export function ArticleHistory({ articleHistory, selectedTicker }: ArticleHistoryProps) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>{selectedTicker} Article History</h2>
        <span>{articleHistory.length} unique articles</span>
      </div>
      {articleHistory.length ? (
        <div className="evidence-list">
          {articleHistory.map(({ article, analyses }) => (
            <article className="evidence-row" key={article.content_hash}>
              <div>
                <ArticleTitle article={article} />
                <p>{article.source ?? article.input_type}</p>
              </div>
              <div className="evidence-meta">
                <span>{article.word_count} words</span>
                <span>
                  {analyses.length} run{analyses.length === 1 ? "" : "s"}
                </span>
                <span className={article.included_in_forecast ? "included" : "excluded"}>
                  {article.included_in_forecast ? "included" : "excluded"}
                </span>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-text">No article history for this ticker yet.</p>
      )}
    </section>
  );
}
