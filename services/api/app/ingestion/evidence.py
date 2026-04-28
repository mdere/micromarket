import re
from dataclasses import dataclass
from decimal import Decimal

from app.ingestion.service import NormalizedArticle


@dataclass(frozen=True)
class EvidenceDecision:
    relevance_score: Decimal
    duplicate_group_id: str | None
    included_in_forecast: bool
    exclusion_reason: str | None


class ArticleEvidencePolicy:
    minimum_relevance = Decimal("0.40000")

    def decide(
        self,
        article: NormalizedArticle,
        ticker: str,
        seen_hashes: set[str],
    ) -> EvidenceDecision:
        duplicate_group_id = article.content_hash if article.content_hash in seen_hashes else None
        relevance_score = self._relevance_score(article, ticker)
        exclusion_reason = None

        has_ticker_evidence = self._has_ticker_evidence(article, ticker)

        if duplicate_group_id is not None:
            exclusion_reason = "Duplicate article content already included in this analysis."
        elif not has_ticker_evidence:
            exclusion_reason = "Article text did not reference the requested ticker."
        elif relevance_score < self.minimum_relevance:
            exclusion_reason = "Article text did not appear relevant enough to the requested ticker."

        return EvidenceDecision(
            relevance_score=relevance_score,
            duplicate_group_id=duplicate_group_id,
            included_in_forecast=exclusion_reason is None,
            exclusion_reason=exclusion_reason,
        )

    def _relevance_score(self, article: NormalizedArticle, ticker: str) -> Decimal:
        ticker_lower = ticker.lower()
        title = article.title or ""
        url = article.url or ""
        text = article.text

        score = Decimal("0")
        if self._contains_token(title, ticker_lower):
            score += Decimal("0.50000")
        if self._contains_token(text, ticker_lower):
            score += Decimal("0.40000")
        if ticker_lower in url.lower():
            score += Decimal("0.20000")
        if self._contains_market_context(text):
            score += Decimal("0.15000")

        return min(score, Decimal("1.00000"))

    def _has_ticker_evidence(self, article: NormalizedArticle, ticker: str) -> bool:
        ticker_lower = ticker.lower()
        return (
            self._contains_token(article.title or "", ticker_lower)
            or self._contains_token(article.text, ticker_lower)
            or ticker_lower in (article.url or "").lower()
        )

    def _contains_token(self, value: str, token: str) -> bool:
        return token in re.findall(r"[a-zA-Z]+", value.lower())

    def _contains_market_context(self, text: str) -> bool:
        market_terms = {
            "analyst",
            "earnings",
            "equity",
            "forecast",
            "market",
            "markets",
            "revenue",
            "shares",
            "stock",
            "stocks",
            "trading",
        }
        tokens = set(re.findall(r"[a-zA-Z]+", text.lower()))
        return bool(tokens.intersection(market_terms))
