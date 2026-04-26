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


class AnalysisResponse(BaseModel):
    id: str
    ticker: str
    status: str
    primary_horizon: str
    message: str
