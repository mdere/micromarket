import re
from dataclasses import dataclass

from app.sentiment.provider import SentimentResult


@dataclass(frozen=True)
class _LexiconEntry:
    sentiment: str
    category: str
    weight: float = 1.0


@dataclass(frozen=True)
class _Signal:
    term: str
    sentiment: str
    category: str
    weight: float


class BaselineSentimentProvider:
    provider_name = "baseline"
    model_name = "sentiment-lexicon-baseline"
    model_version = "0.2.0"

    phrase_lexicon = {
        "beat expectations": _LexiconEntry("positive", "earnings", 1.4),
        "beats expectations": _LexiconEntry("positive", "earnings", 1.4),
        "raised guidance": _LexiconEntry("positive", "guidance", 1.5),
        "margin expansion": _LexiconEntry("positive", "earnings", 1.2),
        "revenue growth": _LexiconEntry("positive", "earnings", 1.2),
        "free cash flow": _LexiconEntry("positive", "earnings", 1.0),
        "market share gains": _LexiconEntry("positive", "demand", 1.2),
        "price target increase": _LexiconEntry("positive", "analyst_action", 1.1),
        "pressure eased": _LexiconEntry("positive", "macro", 1.1),
        "missed expectations": _LexiconEntry("negative", "earnings", 1.4),
        "lowered guidance": _LexiconEntry("negative", "guidance", 1.5),
        "cut guidance": _LexiconEntry("negative", "guidance", 1.5),
        "margin pressure": _LexiconEntry("negative", "earnings", 1.2),
        "demand slowdown": _LexiconEntry("negative", "demand", 1.2),
        "valuation concerns": _LexiconEntry("negative", "valuation", 1.0),
        "regulatory risk": _LexiconEntry("negative", "regulatory", 1.2),
        "price target cut": _LexiconEntry("negative", "analyst_action", 1.1),
        "limited conviction": _LexiconEntry("negative", "uncertainty", 0.8),
    }
    token_lexicon = {
        "accelerated": _LexiconEntry("positive", "demand"),
        "advance": _LexiconEntry("positive", "macro"),
        "advanced": _LexiconEntry("positive", "macro"),
        "backlog": _LexiconEntry("positive", "demand"),
        "beat": _LexiconEntry("positive", "earnings"),
        "beats": _LexiconEntry("positive", "earnings"),
        "breadth": _LexiconEntry("positive", "macro", 0.8),
        "bullish": _LexiconEntry("positive", "analyst_action"),
        "constructive": _LexiconEntry("positive", "analyst_action"),
        "demand": _LexiconEntry("positive", "demand"),
        "eased": _LexiconEntry("positive", "macro"),
        "expand": _LexiconEntry("positive", "earnings"),
        "expanded": _LexiconEntry("positive", "earnings"),
        "growth": _LexiconEntry("positive", "earnings"),
        "improved": _LexiconEntry("positive", "earnings"),
        "improving": _LexiconEntry("positive", "earnings"),
        "outperform": _LexiconEntry("positive", "analyst_action"),
        "positive": _LexiconEntry("positive", "analyst_action"),
        "profit": _LexiconEntry("positive", "earnings"),
        "profitable": _LexiconEntry("positive", "earnings"),
        "resilient": _LexiconEntry("positive", "demand"),
        "strong": _LexiconEntry("positive", "demand"),
        "stronger": _LexiconEntry("positive", "demand"),
        "stable": _LexiconEntry("positive", "earnings", 0.7),
        "upside": _LexiconEntry("positive", "valuation"),
        "adoption": _LexiconEntry("positive", "product"),
        "approved": _LexiconEntry("positive", "regulatory"),
        "bearish": _LexiconEntry("negative", "analyst_action"),
        "cautious": _LexiconEntry("negative", "uncertainty"),
        "concern": _LexiconEntry("negative", "uncertainty"),
        "concerns": _LexiconEntry("negative", "uncertainty"),
        "constraints": _LexiconEntry("negative", "supply"),
        "decline": _LexiconEntry("negative", "earnings"),
        "declined": _LexiconEntry("negative", "earnings"),
        "delay": _LexiconEntry("negative", "supply"),
        "delays": _LexiconEntry("negative", "supply"),
        "downgrade": _LexiconEntry("negative", "analyst_action"),
        "falling": _LexiconEntry("negative", "macro"),
        "investigation": _LexiconEntry("negative", "regulatory"),
        "limited": _LexiconEntry("negative", "uncertainty", 0.8),
        "loss": _LexiconEntry("negative", "earnings"),
        "miss": _LexiconEntry("negative", "earnings"),
        "missed": _LexiconEntry("negative", "earnings"),
        "negative": _LexiconEntry("negative", "analyst_action"),
        "pressure": _LexiconEntry("negative", "earnings"),
        "recall": _LexiconEntry("negative", "product"),
        "risk": _LexiconEntry("negative", "uncertainty"),
        "risks": _LexiconEntry("negative", "uncertainty"),
        "slowdown": _LexiconEntry("negative", "demand"),
        "uncertainty": _LexiconEntry("negative", "uncertainty"),
        "volatile": _LexiconEntry("negative", "uncertainty", 0.7),
        "weak": _LexiconEntry("negative", "demand"),
        "weaker": _LexiconEntry("negative", "demand"),
        "warned": _LexiconEntry("negative", "guidance"),
        "warning": _LexiconEntry("negative", "guidance"),
    }
    negation_terms = {"no", "not", "without", "lacks", "lacking", "never"}
    uncertainty_terms = {"could", "may", "might", "potential", "possible", "unclear"}

    def score_article(self, article_text: str, ticker: str) -> SentimentResult:
        tokens = self._tokenize(article_text)
        signals = self._signals(article_text, tokens)
        positive_weight = sum(signal.weight for signal in signals if signal.sentiment == "positive")
        negative_weight = sum(signal.weight for signal in signals if signal.sentiment == "negative")
        total_weight = positive_weight + negative_weight
        score = 0.0
        if total_weight > 0:
            score = (positive_weight - negative_weight) / total_weight

        positive_count = sum(1 for signal in signals if signal.sentiment == "positive")
        negative_count = sum(1 for signal in signals if signal.sentiment == "negative")
        uncertainty_count = sum(1 for token in tokens if token in self.uncertainty_terms)
        label = self._label(score, positive_count, negative_count)
        confidence = self._confidence(
            score=score,
            signal_count=len(signals),
            token_count=len(tokens),
            uncertainty_count=uncertainty_count,
            label=label,
        )
        drivers = self._drivers(signals)
        snippets = self._evidence_snippets(article_text, {signal.term for signal in signals}, ticker)
        limitations = self._limitations(
            signal_count=len(signals),
            token_count=len(tokens),
            uncertainty_count=uncertainty_count,
            label=label,
        )

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

    def _signals(self, text: str, tokens: list[str]) -> list[_Signal]:
        signals = []
        lowered = text.lower()
        for phrase, entry in self.phrase_lexicon.items():
            for match in re.finditer(rf"\b{re.escape(phrase)}\b", lowered):
                sentiment = entry.sentiment
                weight = entry.weight
                prefix_tokens = self._tokenize(lowered[: match.start()])
                if self._has_recent_negation(prefix_tokens):
                    sentiment = "negative" if entry.sentiment == "positive" else "positive"
                    weight *= 0.8
                signals.append(
                    _Signal(
                        term=phrase,
                        sentiment=sentiment,
                        category=entry.category,
                        weight=weight,
                    )
                )

        for index, token in enumerate(tokens):
            entry = self.token_lexicon.get(token)
            if entry is None:
                continue
            sentiment = entry.sentiment
            weight = entry.weight
            if self._is_negated(tokens, index):
                sentiment = "negative" if entry.sentiment == "positive" else "positive"
                weight *= 0.8
            signals.append(
                _Signal(
                    term=token,
                    sentiment=sentiment,
                    category=entry.category,
                    weight=weight,
                )
            )
        return signals

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z]+", text.lower())

    def _is_negated(self, tokens: list[str], index: int) -> bool:
        window_start = max(index - 3, 0)
        return any(token in self.negation_terms for token in tokens[window_start:index])

    def _has_recent_negation(self, tokens: list[str]) -> bool:
        return any(token in self.negation_terms for token in tokens[-3:])

    def _label(self, score: float, positive_count: int, negative_count: int) -> str:
        if positive_count >= 2 and negative_count >= 2 and abs(score) <= 0.4:
            return "mixed"
        if score > 0.2:
            return "positive"
        if score < -0.2:
            return "negative"
        return "neutral"

    def _confidence(
        self,
        *,
        score: float,
        signal_count: int,
        token_count: int,
        uncertainty_count: int,
        label: str,
    ) -> float:
        if signal_count == 0:
            return 0.2
        confidence = 0.3 + min(signal_count, 8) * 0.07 + min(abs(score), 1.0) * 0.18
        if label == "mixed":
            confidence -= 0.08
        if token_count < 40:
            confidence -= 0.12
        confidence -= min(uncertainty_count * 0.04, 0.16)
        return max(0.2, min(confidence, 0.86))

    def _drivers(self, signals: list[_Signal]) -> list[str]:
        if not signals:
            return []
        categories: dict[str, dict[str, set[str]]] = {}
        for signal in signals:
            category = categories.setdefault(signal.category, {"positive": set(), "negative": set()})
            category[signal.sentiment].add(signal.term)

        drivers = []
        for category, sentiment_terms in sorted(categories.items()):
            parts = []
            for sentiment in ("positive", "negative"):
                terms = sorted(sentiment_terms[sentiment])
                if terms:
                    parts.append(f"{sentiment}: {', '.join(terms[:4])}")
            drivers.append(f"{category}: {'; '.join(parts)}")
        return drivers

    def _evidence_snippets(self, text: str, keywords: set[str], ticker: str) -> list[str]:
        if not keywords:
            return []
        snippets = []
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_tokens = set(self._tokenize(sentence))
            if (
                any(keyword in sentence_lower for keyword in keywords if " " in keyword)
                or sentence_tokens.intersection(keywords)
                or ticker.lower() in sentence_tokens
            ):
                snippets.append(sentence.strip())
            if len(snippets) >= 3:
                break
        return snippets

    def _limitations(
        self,
        *,
        signal_count: int,
        token_count: int,
        uncertainty_count: int,
        label: str,
    ) -> list[str]:
        limitations = []
        if signal_count == 0:
            limitations.append("No baseline sentiment keywords were found.")
        if token_count < 40:
            limitations.append("Article text is short, so sentiment confidence is limited.")
        if label == "mixed":
            limitations.append("Positive and negative baseline signals were both present.")
        if uncertainty_count > 0:
            limitations.append("Uncertainty language reduced baseline sentiment confidence.")
        return limitations
