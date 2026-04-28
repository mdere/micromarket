"use client";

import { useMemo, useState } from "react";

import type { ArticleResponse } from "@/lib/micromarket-types";
import { EvidenceList } from "./evidence-list";

type EvidenceFilter = "all" | "included" | "excluded" | "duplicates";

const filterLabels: Record<EvidenceFilter, string> = {
  all: "All",
  included: "Included",
  excluded: "Excluded",
  duplicates: "Duplicates"
};

export function EvidencePanel({ articles }: { articles: ArticleResponse[] }) {
  const [activeFilter, setActiveFilter] = useState<EvidenceFilter>("all");
  const counts = useMemo(() => countEvidence(articles), [articles]);
  const filteredArticles = useMemo(() => {
    if (activeFilter === "included") {
      return articles.filter((article) => article.included_in_forecast);
    }
    if (activeFilter === "excluded") {
      return articles.filter((article) => !article.included_in_forecast);
    }
    if (activeFilter === "duplicates") {
      return articles.filter((article) => article.duplicate_group_id);
    }
    return articles;
  }, [activeFilter, articles]);

  return (
    <section className="panel">
      <div className="section-heading">
        <h2>Selected Run Evidence</h2>
        <span>{articles.length} articles</span>
      </div>
      <div className="segmented-control" aria-label="Evidence filter">
        {(Object.keys(filterLabels) as EvidenceFilter[]).map((filter) => (
          <button
            className={activeFilter === filter ? "active" : ""}
            key={filter}
            type="button"
            onClick={() => setActiveFilter(filter)}
          >
            {filterLabels[filter]} <span>{counts[filter]}</span>
          </button>
        ))}
      </div>
      <EvidenceList
        articles={filteredArticles}
        emptyMessage={emptyMessageFor(activeFilter)}
      />
    </section>
  );
}

function countEvidence(articles: ArticleResponse[]) {
  return {
    all: articles.length,
    included: articles.filter((article) => article.included_in_forecast).length,
    excluded: articles.filter((article) => !article.included_in_forecast).length,
    duplicates: articles.filter((article) => article.duplicate_group_id).length
  };
}

function emptyMessageFor(filter: EvidenceFilter) {
  if (filter === "included") {
    return "No included evidence for this run.";
  }
  if (filter === "excluded") {
    return "No excluded evidence for this run.";
  }
  if (filter === "duplicates") {
    return "No duplicate evidence for this run.";
  }
  return "No evidence loaded for this run.";
}
