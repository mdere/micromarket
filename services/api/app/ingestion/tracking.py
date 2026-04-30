from dataclasses import dataclass, field

from app.ingestion.entities import ExtractedEntity


@dataclass(frozen=True)
class TrackingNeed:
    suggested_symbol: str | None
    tracking_type: str
    reason: str
    evidence_snippets: list[str] = field(default_factory=list)
    priority_score: float = 0.50
    status: str = "suggested"
    provider: str = "deterministic"
    model_name: str = "tracking-needs-baseline"
    model_version: str = "0.1.0"


class TrackingNeedGenerator:
    provider = "deterministic"
    model_name = "tracking-needs-baseline"
    model_version = "0.1.0"

    def generate(self, extracted: ExtractedEntity) -> TrackingNeed:
        tracking_type = _tracking_type(extracted)
        priority_score = _priority_score(extracted, tracking_type)
        reason = _reason(extracted, tracking_type)
        return TrackingNeed(
            suggested_symbol=extracted.symbol,
            tracking_type=tracking_type,
            reason=reason,
            evidence_snippets=extracted.evidence_snippets[:3],
            priority_score=priority_score,
            provider=self.provider,
            model_name=self.model_name,
            model_version=self.model_version,
        )


def _tracking_type(extracted: ExtractedEntity) -> str:
    if extracted.relationship_type in {"supplier", "customer", "competitor"}:
        return extracted.relationship_type
    if extracted.entity_type == "asset" and extracted.symbol:
        return "related_ticker"
    if extracted.entity_type in {"product", "theme", "keyword"}:
        return "product_theme"
    if extracted.entity_type == "sector":
        return "macro_theme"
    return "unknown"


def _priority_score(extracted: ExtractedEntity, tracking_type: str) -> float:
    base_scores = {
        "related_ticker": 0.90,
        "supplier": 0.85,
        "customer": 0.80,
        "competitor": 0.80,
        "product_theme": 0.65,
        "macro_theme": 0.55,
        "unknown": 0.40,
    }
    evidence_bonus = min(0.05 * len(extracted.evidence_snippets), 0.10)
    return round(min(base_scores.get(tracking_type, 0.40) + evidence_bonus, 0.99), 5)


def _reason(extracted: ExtractedEntity, tracking_type: str) -> str:
    if extracted.symbol:
        target = f"{extracted.name} ({extracted.symbol})"
    else:
        target = extracted.name
    relationship = extracted.relationship_type.replace("_", " ")
    if tracking_type == "related_ticker":
        return f"{target} was mentioned as a related ticker/entity for the primary asset."
    if tracking_type in {"supplier", "customer", "competitor"}:
        return f"{target} appeared as a {relationship} connected to the primary asset."
    if tracking_type == "product_theme":
        return f"{target} appeared as a product/theme exposure connected to the primary asset."
    if tracking_type == "macro_theme":
        return f"{target} appeared as a broader market or sector theme."
    return f"{target} was mentioned with the primary asset."
