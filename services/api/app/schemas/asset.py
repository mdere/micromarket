from pydantic import BaseModel, Field


class AssetOnboardRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    name: str | None = None


class AssetWorkspaceResponse(BaseModel):
    id: str
    symbol: str
    name: str | None = None
    asset_type: str
    currency: str | None = None
    analysis_count: int
    market_history_count: int
    history_start_date: str | None = None
    history_end_date: str | None = None
    latest_analysis_at: str | None = None
    onboarding_status: str
