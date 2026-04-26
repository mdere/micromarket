from dataclasses import dataclass, field


@dataclass(frozen=True)
class ForecastResult:
    horizon: str
    predicted_direction: str
    predicted_percent_change: float | None
    confidence: float
    top_factors: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    model_name: str = "forecast-rules"
    model_version: str = "0.1.0"
