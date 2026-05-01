from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.db.models import Asset, utc_now
from app.db.session import get_db
from app.market_data.dependencies import get_market_data_provider
from app.market_data.history import ensure_market_history
from app.market_data.provider import MarketDataProvider
from app.market_data.yfinance_provider import MarketDataProviderError
from app.schemas.asset import AssetOnboardRequest, AssetWorkspaceResponse

router = APIRouter()


@router.get("", response_model=list[AssetWorkspaceResponse])
def list_asset_workspaces(
    query: str | None = Query(default=None, min_length=1, max_length=64),
    db: Session = Depends(get_db),
) -> list[AssetWorkspaceResponse]:
    statement = (
        select(Asset)
        .options(
            selectinload(Asset.analyses),
            selectinload(Asset.market_price_history),
            selectinload(Asset.ticker_contexts),
        )
        .order_by(Asset.symbol)
        .limit(50)
    )
    if query:
        normalized_query = f"%{query.upper().strip()}%"
        statement = statement.where(
            Asset.symbol.ilike(normalized_query) | Asset.name.ilike(normalized_query)
        )
    assets = db.scalars(statement).all()
    return [_to_workspace_response(asset) for asset in assets]


@router.post("/onboard", response_model=AssetWorkspaceResponse, status_code=status.HTTP_201_CREATED)
def onboard_asset_workspace(
    payload: AssetOnboardRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    market_data_provider: MarketDataProvider = Depends(get_market_data_provider),
) -> AssetWorkspaceResponse:
    symbol = payload.symbol.upper().strip()
    asset = db.scalar(select(Asset).where(Asset.symbol == symbol))
    if asset is None:
        asset = Asset(
            symbol=symbol,
            name=payload.name,
            asset_type="equity",
            currency="USD",
        )
        db.add(asset)
        db.flush()
    elif asset.name is None and payload.name:
        asset.name = payload.name

    try:
        ensure_market_history(
            db=db,
            asset=asset,
            ticker=symbol,
            provider=market_data_provider,
            analysis_as_of=utc_now(),
            lookback_days=settings.market_lookback_days,
        )
    except MarketDataProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.commit()
    db.refresh(asset)
    asset = db.scalar(
        select(Asset)
        .where(Asset.id == asset.id)
        .options(
            selectinload(Asset.analyses),
            selectinload(Asset.market_price_history),
            selectinload(Asset.ticker_contexts),
        )
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset workspace not found after onboarding.")
    return _to_workspace_response(asset)


def _to_workspace_response(asset: Asset) -> AssetWorkspaceResponse:
    latest_analysis_at = max(
        (analysis.created_at for analysis in asset.analyses),
        default=None,
    )
    history_start_date = min(
        (context.history_start_date for context in asset.ticker_contexts if context.history_start_date),
        default=None,
    )
    history_end_date = max(
        (context.history_end_date for context in asset.ticker_contexts if context.history_end_date),
        default=None,
    )
    return AssetWorkspaceResponse(
        id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        asset_type=asset.asset_type,
        currency=asset.currency,
        analysis_count=len(asset.analyses),
        market_history_count=len(asset.market_price_history),
        history_start_date=history_start_date.isoformat() if history_start_date else None,
        history_end_date=history_end_date.isoformat() if history_end_date else None,
        latest_analysis_at=latest_analysis_at.isoformat() if latest_analysis_at else None,
        onboarding_status="onboarded" if asset.ticker_contexts else "created",
    )
