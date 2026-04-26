from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.db.models import (
    Analysis,
    AnalysisArticle,
    Article,
    Asset,
    MarketQuote,
    SentimentAggregate,
    SentimentRun,
    utc_now,
)
from app.db.session import get_db
from app.ingestion.service import ArticleIngestionService
from app.market_data.dependencies import get_market_data_provider
from app.market_data.provider import MarketDataProvider
from app.market_data.yfinance_provider import MarketDataProviderError
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.sentiment.dependencies import get_sentiment_provider
from app.sentiment.provider import SentimentProvider
from app.storage import ArtifactStore

router = APIRouter()


@router.post("", response_model=AnalysisResponse, status_code=201)
def create_analysis(
    payload: AnalysisCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    market_data_provider: MarketDataProvider = Depends(get_market_data_provider),
    sentiment_provider: SentimentProvider = Depends(get_sentiment_provider),
) -> AnalysisResponse:
    ticker = payload.ticker.upper().strip()
    manual_articles = [article for article in payload.articles if article.text and article.text.strip()]

    if not manual_articles:
        raise HTTPException(
            status_code=400,
            detail="At least one manual article with text is required for the first vertical slice.",
        )

    asset = db.scalar(select(Asset).where(Asset.symbol == ticker))
    if asset is None:
        asset = Asset(symbol=ticker, asset_type="equity", currency="USD")
        db.add(asset)
        db.flush()

    input_mode = "manual_text"
    analysis = Analysis(
        asset_id=asset.id,
        status="running",
        primary_horizon=payload.primary_horizon,
        input_mode=input_mode,
        limitations=[
            "Research-only output; not financial advice.",
            "This first vertical slice stores manual article evidence only.",
        ],
    )
    db.add(analysis)
    db.flush()

    try:
        quote = market_data_provider.get_quote(ticker)
    except MarketDataProviderError as exc:
        analysis.status = "failed"
        analysis.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.add(
        MarketQuote(
            asset_id=asset.id,
            analysis_id=analysis.id,
            provider=quote.provider,
            price=quote.price,
            previous_close=quote.previous_close,
            open=quote.open,
            day_high=quote.day_high,
            day_low=quote.day_low,
            volume=quote.volume,
            market_cap=quote.market_cap,
            fifty_two_week_high=quote.fifty_two_week_high,
            fifty_two_week_low=quote.fifty_two_week_low,
            moving_average_50=quote.moving_average_50,
            moving_average_200=quote.moving_average_200,
            beta=quote.beta,
            pe_ratio=quote.pe_ratio,
            quote_time=quote.quote_time,
        )
    )

    ingestion = ArticleIngestionService()
    artifacts = ArtifactStore(settings.artifact_root)
    sentiment_labels: list[str] = []
    sentiment_scores: list[Decimal] = []
    included_article_count = 0

    for article_input in manual_articles:
        normalized = ingestion.normalize_text(
            article_input.text or "", title=article_input.title, source=article_input.source
        )
        artifact_path = artifacts.write_article_text(normalized.content_hash, normalized.text)
        article = Article(
            asset_id=asset.id,
            title=normalized.title,
            source=normalized.source,
            url=article_input.url,
            input_type="manual_text",
            raw_artifact_path=artifact_path,
            extracted_text_artifact_path=artifact_path,
            content_hash=normalized.content_hash,
            language="en",
            word_count=len(normalized.text.split()),
            retrieved_at=utc_now(),
        )
        db.add(article)
        db.flush()
        db.add(
            AnalysisArticle(
                analysis_id=analysis.id,
                article_id=article.id,
                relevance_score=None,
                included_in_forecast=True,
            )
        )
        sentiment = sentiment_provider.score_article(normalized.text, ticker)
        sentiment_labels.append(sentiment.label)
        sentiment_score = Decimal(str(sentiment.score))
        sentiment_scores.append(sentiment_score)
        included_article_count += 1
        db.add(
            SentimentRun(
                analysis_id=analysis.id,
                article_id=article.id,
                provider=sentiment.provider,
                model_name=sentiment.model_name,
                model_version=sentiment.model_version,
                sentiment_label=sentiment.label,
                sentiment_score=sentiment_score,
                confidence_score=Decimal(str(sentiment.confidence)),
                drivers=sentiment.drivers,
                evidence_snippets=sentiment.evidence_snippets,
                limitations=sentiment.limitations,
            )
        )

    db.add(
        _build_sentiment_aggregate(
            analysis_id=analysis.id,
            labels=sentiment_labels,
            scores=sentiment_scores,
            included_article_count=included_article_count,
        )
    )

    analysis.status = "completed"
    analysis.completed_at = utc_now()
    db.commit()

    persisted = _get_analysis(db, analysis.id)
    return _to_response(persisted, "Analysis created with persisted manual article evidence.")


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisResponse:
    analysis = _get_analysis(db, analysis_id)
    return _to_response(analysis, "Analysis retrieved.")


@router.get("", response_model=list[AnalysisResponse])
def list_analyses(db: Session = Depends(get_db)) -> list[AnalysisResponse]:
    analyses = db.scalars(
        select(Analysis)
        .options(selectinload(Analysis.asset), selectinload(Analysis.articles))
        .options(selectinload(Analysis.market_quotes))
        .options(selectinload(Analysis.sentiment_runs))
        .options(selectinload(Analysis.sentiment_aggregate))
        .order_by(Analysis.created_at.desc())
        .limit(25)
    ).all()
    return [_to_response(analysis, "Analysis retrieved.") for analysis in analyses]


def _get_analysis(db: Session, analysis_id: str) -> Analysis:
    analysis = db.scalar(
        select(Analysis)
        .where(Analysis.id == analysis_id)
        .options(
            selectinload(Analysis.asset),
            selectinload(Analysis.articles),
            selectinload(Analysis.market_quotes),
            selectinload(Analysis.sentiment_runs),
            selectinload(Analysis.sentiment_aggregate),
        )
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis


def _to_response(analysis: Analysis, message: str) -> AnalysisResponse:
    market_quote = max(analysis.market_quotes, key=lambda quote: quote.retrieved_at, default=None)

    return AnalysisResponse(
        id=analysis.id,
        ticker=analysis.asset.symbol,
        status=analysis.status,
        primary_horizon=analysis.primary_horizon,
        input_mode=analysis.input_mode,
        message=message,
        limitations=analysis.limitations or [],
        articles=[
            {
                "id": article.id,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "input_type": article.input_type,
                "content_hash": article.content_hash,
                "word_count": article.word_count,
                "raw_artifact_path": article.raw_artifact_path,
            }
            for article in analysis.articles
        ],
        market_quote=(
            {
                "id": market_quote.id,
                "provider": market_quote.provider,
                "price": _decimal_to_str(market_quote.price),
                "previous_close": _decimal_to_str(market_quote.previous_close),
                "open": _decimal_to_str(market_quote.open),
                "day_high": _decimal_to_str(market_quote.day_high),
                "day_low": _decimal_to_str(market_quote.day_low),
                "volume": market_quote.volume,
                "market_cap": market_quote.market_cap,
                "quote_time": _datetime_to_str(market_quote.quote_time),
                "retrieved_at": _datetime_to_str(market_quote.retrieved_at) or "",
            }
            if market_quote is not None
            else None
        ),
        sentiment_runs=[
            {
                "id": run.id,
                "article_id": run.article_id,
                "provider": run.provider,
                "model_name": run.model_name,
                "model_version": run.model_version,
                "sentiment_label": run.sentiment_label,
                "sentiment_score": _decimal_to_str(run.sentiment_score) or "0",
                "confidence_score": _decimal_to_str(run.confidence_score) or "0",
                "drivers": run.drivers or [],
                "evidence_snippets": run.evidence_snippets or [],
                "limitations": run.limitations or [],
            }
            for run in analysis.sentiment_runs
        ],
        sentiment_aggregate=(
            {
                "article_count": analysis.sentiment_aggregate.article_count,
                "included_article_count": analysis.sentiment_aggregate.included_article_count,
                "positive_count": analysis.sentiment_aggregate.positive_count,
                "neutral_count": analysis.sentiment_aggregate.neutral_count,
                "negative_count": analysis.sentiment_aggregate.negative_count,
                "mixed_count": analysis.sentiment_aggregate.mixed_count,
                "aggregate_score": _decimal_to_str(analysis.sentiment_aggregate.aggregate_score),
                "agreement_score": _decimal_to_str(analysis.sentiment_aggregate.agreement_score),
                "evidence_strength_score": _decimal_to_str(
                    analysis.sentiment_aggregate.evidence_strength_score
                ),
                "summary": analysis.sentiment_aggregate.summary,
            }
            if analysis.sentiment_aggregate is not None
            else None
        ),
    )


def _decimal_to_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _datetime_to_str(value: object | None) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _build_sentiment_aggregate(
    analysis_id: str,
    labels: list[str],
    scores: list[Decimal],
    included_article_count: int,
) -> SentimentAggregate:
    article_count = len(labels)
    positive_count = labels.count("positive")
    neutral_count = labels.count("neutral")
    negative_count = labels.count("negative")
    mixed_count = labels.count("mixed")
    aggregate_score = sum(scores, Decimal("0")) / Decimal(max(len(scores), 1))
    dominant_count = max(positive_count, neutral_count, negative_count, mixed_count, 0)
    agreement_score = Decimal(str(dominant_count / max(article_count, 1)))
    evidence_strength_score = min(
        Decimal("1"),
        Decimal(str(included_article_count)) / Decimal("3"),
    )
    summary = _sentiment_summary(
        article_count=article_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        aggregate_score=aggregate_score,
    )
    return SentimentAggregate(
        analysis_id=analysis_id,
        article_count=article_count,
        included_article_count=included_article_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        mixed_count=mixed_count,
        aggregate_score=aggregate_score,
        agreement_score=agreement_score,
        evidence_strength_score=evidence_strength_score,
        summary=summary,
    )


def _sentiment_summary(
    article_count: int,
    positive_count: int,
    neutral_count: int,
    negative_count: int,
    aggregate_score: Decimal,
) -> str:
    if aggregate_score > Decimal("0.2"):
        leaning = "positive"
    elif aggregate_score < Decimal("-0.2"):
        leaning = "negative"
    else:
        leaning = "neutral"
    return (
        f"Baseline sentiment is {leaning} across {article_count} article(s): "
        f"{positive_count} positive, {neutral_count} neutral, {negative_count} negative."
    )
