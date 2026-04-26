from uuid import uuid4

from fastapi import APIRouter

from app.schemas.analysis import AnalysisCreate, AnalysisResponse

router = APIRouter()


@router.post("", response_model=AnalysisResponse, status_code=201)
def create_analysis(payload: AnalysisCreate) -> AnalysisResponse:
    analysis_id = str(uuid4())
    return AnalysisResponse(
        id=analysis_id,
        ticker=payload.ticker.upper(),
        status="created",
        primary_horizon=payload.primary_horizon,
        message="Analysis scaffold created. Pipeline implementation is next.",
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str) -> AnalysisResponse:
    return AnalysisResponse(
        id=analysis_id,
        ticker="TBD",
        status="placeholder",
        primary_horizon="3_trading_days",
        message="Analysis retrieval scaffold. Database persistence is next.",
    )
