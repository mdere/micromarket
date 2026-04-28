import type { ArticleResponse } from "@/lib/micromarket-types";
import { formatScore } from "@/lib/format";

export function EvidenceList({
  articles,
  emptyMessage = "No evidence loaded."
}: {
  articles: ArticleResponse[];
  emptyMessage?: string;
}) {
  if (!articles.length) {
    return <p className="muted-text">{emptyMessage}</p>;
  }

  return (
    <div className="evidence-list">
      {articles.map((article) => (
        <article className="evidence-row" key={article.id}>
          <div>
            <ArticleTitle article={article} />
            <p>{article.source ?? article.input_type}</p>
          </div>
          <div className="evidence-meta">
            <span>{article.word_count} words</span>
            <span>relevance {formatScore(article.relevance_score)}</span>
            <span className={article.included_in_forecast ? "included" : "excluded"}>
              {article.included_in_forecast ? "included" : "excluded"}
            </span>
          </div>
          {article.exclusion_reason ? (
            <p className="warning-text">{article.exclusion_reason}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}

export function ArticleTitle({ article }: { article: ArticleResponse }) {
  const label = article.title ?? article.url ?? "Untitled article";

  if (!article.url) {
    return <strong>{label}</strong>;
  }

  return (
    <strong>
      <a href={article.url} rel="noreferrer" target="_blank">
        {label}
      </a>
    </strong>
  );
}
