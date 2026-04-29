from dataclasses import dataclass, field
from typing import Protocol


class SentimentProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class SentimentResult:
    label: str
    score: float
    confidence: float
    drivers: list[str] = field(default_factory=list)
    evidence_snippets: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    provider: str = "baseline"
    model_name: str = "sentiment-baseline"
    model_version: str = "0.1.0"


class SentimentProvider(Protocol):
    def score_article(self, article_text: str, ticker: str) -> SentimentResult:
        """Score one article for ticker-relevant sentiment."""
