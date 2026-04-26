from pydantic import BaseModel, Field


class ArticleInput(BaseModel):
    title: str | None = None
    source: str | None = None
    url: str | None = None
    text: str | None = None


class AnalysisCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    primary_horizon: str = "3_trading_days"
    articles: list[ArticleInput] = Field(default_factory=list)


class ArticleResponse(BaseModel):
    id: str
    title: str | None
    source: str | None
    url: str | None
    input_type: str
    content_hash: str
    word_count: int
    raw_artifact_path: str | None


class AnalysisResponse(BaseModel):
    id: str
    ticker: str
    status: str
    primary_horizon: str
    input_mode: str = "manual_text"
    message: str
    limitations: list[str] = Field(default_factory=list)
    articles: list[ArticleResponse] = Field(default_factory=list)
