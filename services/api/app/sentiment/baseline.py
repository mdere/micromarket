import re

from app.sentiment.provider import SentimentResult


class BaselineSentimentProvider:
    provider_name = "baseline"
    model_name = "sentiment-lexicon-baseline"
    model_version = "0.1.0"

    positive_terms = {
        "advance",
        "advanced",
        "beat",
        "beats",
        "bullish",
        "constructive",
        "demand",
        "eased",
        "expand",
        "expanded",
        "growth",
        "improved",
        "improving",
        "outperform",
        "positive",
        "profit",
        "profitable",
        "resilient",
        "strong",
        "stronger",
        "stable",
        "upside",
    }
    negative_terms = {
        "bearish",
        "cautious",
        "concern",
        "concerns",
        "decline",
        "declined",
        "downgrade",
        "falling",
        "loss",
        "miss",
        "missed",
        "negative",
        "pressure",
        "risk",
        "risks",
        "slowdown",
        "uncertainty",
        "weak",
        "weaker",
        "warned",
        "warning",
    }

    def score_article(self, article_text: str, ticker: str) -> SentimentResult:
        tokens = self._tokenize(article_text)
        positive_hits = [token for token in tokens if token in self.positive_terms]
        negative_hits = [token for token in tokens if token in self.negative_terms]
        hit_count = len(positive_hits) + len(negative_hits)
        denominator = max(hit_count, 1)
        score = (len(positive_hits) - len(negative_hits)) / denominator

        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"

        confidence = min(0.25 + hit_count / 10, 0.8)
        drivers = self._drivers(positive_hits, negative_hits)
        snippets = self._evidence_snippets(article_text, set(positive_hits + negative_hits), ticker)
        limitations = []
        if hit_count == 0:
            limitations.append("No baseline sentiment keywords were found.")
        if len(tokens) < 40:
            limitations.append("Article text is short, so sentiment confidence is limited.")

        return SentimentResult(
            label=label,
            score=round(score, 5),
            confidence=round(confidence, 5),
            drivers=drivers,
            evidence_snippets=snippets,
            limitations=limitations,
            provider=self.provider_name,
            model_name=self.model_name,
            model_version=self.model_version,
        )

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z]+", text.lower())

    def _drivers(self, positive_hits: list[str], negative_hits: list[str]) -> list[str]:
        drivers = []
        if positive_hits:
            drivers.append(f"Positive terms: {', '.join(sorted(set(positive_hits)))}")
        if negative_hits:
            drivers.append(f"Negative terms: {', '.join(sorted(set(negative_hits)))}")
        return drivers

    def _evidence_snippets(self, text: str, keywords: set[str], ticker: str) -> list[str]:
        if not keywords:
            return []
        snippets = []
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            sentence_tokens = set(self._tokenize(sentence))
            if sentence_tokens.intersection(keywords) or ticker.lower() in sentence_tokens:
                snippets.append(sentence.strip())
            if len(snippets) >= 3:
                break
        return snippets
