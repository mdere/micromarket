from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class ExtractedEntity:
    entity_type: str
    name: str
    canonical_name: str
    symbol: str | None = None
    aliases: list[str] = field(default_factory=list)
    relationship_type: str = "mentioned_with"
    confidence: float = 0.70
    evidence_snippets: list[str] = field(default_factory=list)
    provider: str = "deterministic"
    model_name: str = "entity-alias-baseline"
    model_version: str = "0.1.0"


@dataclass(frozen=True)
class EntityDefinition:
    entity_type: str
    name: str
    canonical_name: str
    aliases: tuple[str, ...]
    symbol: str | None = None
    relationship_type: str = "mentioned_with"
    confidence: float = 0.70


class DeterministicEntityExtractor:
    provider = "deterministic"
    model_name = "entity-alias-baseline"
    model_version = "0.1.0"

    _entities = (
        EntityDefinition(
            entity_type="asset",
            name="NVIDIA",
            canonical_name="nvidia",
            symbol="NVDA",
            aliases=("NVDA", "NVIDIA", "Nvidia Corporation"),
            relationship_type="competitor",
            confidence=0.90,
        ),
        EntityDefinition(
            entity_type="asset",
            name="AMD",
            canonical_name="advanced micro devices",
            symbol="AMD",
            aliases=("AMD", "Advanced Micro Devices"),
            relationship_type="competitor",
            confidence=0.90,
        ),
        EntityDefinition(
            entity_type="asset",
            name="TSMC",
            canonical_name="taiwan semiconductor manufacturing company",
            symbol="TSM",
            aliases=(
                "TSMC",
                "TSM",
                "Taiwan Semiconductor",
                "Taiwan Semiconductor Manufacturing Company",
            ),
            relationship_type="supplier",
            confidence=0.90,
        ),
        EntityDefinition(
            entity_type="asset",
            name="Samsung",
            canonical_name="samsung",
            symbol="SSNLF",
            aliases=("Samsung", "Samsung Electronics", "SSNLF"),
            relationship_type="supplier",
            confidence=0.85,
        ),
        EntityDefinition(
            entity_type="company",
            name="Microsoft",
            canonical_name="microsoft",
            symbol="MSFT",
            aliases=("Microsoft", "MSFT", "Azure"),
            relationship_type="customer",
            confidence=0.80,
        ),
        EntityDefinition(
            entity_type="company",
            name="Amazon",
            canonical_name="amazon",
            symbol="AMZN",
            aliases=("Amazon", "AWS", "Amazon Web Services", "AMZN"),
            relationship_type="customer",
            confidence=0.80,
        ),
        EntityDefinition(
            entity_type="product",
            name="HBM",
            canonical_name="high bandwidth memory",
            aliases=("HBM", "high bandwidth memory", "HBM3", "HBM3E"),
            relationship_type="product_exposure",
            confidence=0.85,
        ),
        EntityDefinition(
            entity_type="theme",
            name="AI chips",
            canonical_name="ai chips",
            aliases=("AI chip", "AI chips", "AI accelerator", "AI accelerators", "GPU"),
            relationship_type="product_exposure",
            confidence=0.75,
        ),
        EntityDefinition(
            entity_type="theme",
            name="Foundry capacity",
            canonical_name="foundry capacity",
            aliases=("foundry", "foundry capacity", "wafer capacity", "chip fabrication"),
            relationship_type="product_exposure",
            confidence=0.75,
        ),
        EntityDefinition(
            entity_type="theme",
            name="Earnings",
            canonical_name="earnings",
            aliases=("earnings", "quarterly results", "revenue", "margin", "guidance"),
            relationship_type="mentioned_with",
            confidence=0.70,
        ),
    )

    def extract(self, text: str, ticker: str) -> list[ExtractedEntity]:
        normalized_ticker = ticker.upper().strip()
        sentences = _sentences(text)
        results: list[ExtractedEntity] = []
        seen: set[tuple[str, str]] = set()

        for definition in self._entities:
            if definition.symbol == normalized_ticker:
                continue
            snippets = _matching_snippets(sentences, definition.aliases)
            if not snippets:
                continue
            key = (definition.entity_type, definition.canonical_name)
            if key in seen:
                continue
            seen.add(key)
            results.append(
                ExtractedEntity(
                    entity_type=definition.entity_type,
                    name=definition.name,
                    canonical_name=definition.canonical_name,
                    symbol=definition.symbol,
                    aliases=list(definition.aliases),
                    relationship_type=definition.relationship_type,
                    confidence=definition.confidence,
                    evidence_snippets=snippets[:3],
                    provider=self.provider,
                    model_name=self.model_name,
                    model_version=self.model_version,
                )
            )

        return results


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _matching_snippets(sentences: list[str], aliases: tuple[str, ...]) -> list[str]:
    snippets: list[str] = []
    for sentence in sentences:
        if any(_contains_alias(sentence, alias) for alias in aliases):
            snippets.append(sentence)
    return snippets


def _contains_alias(text: str, alias: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None
