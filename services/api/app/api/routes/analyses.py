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
    ForecastRun,
    MarketQuote,
    SentimentAggregate,
    SentimentRun,
    utc_now,
)
from app.db.session import get_db
from app.forecasting.dependencies import get_forecast_provider
from app.forecasting.provider import ForecastInput, ForecastProvider
from app.ingestion.dependencies import get_url_extraction_provider
from app.ingestion.evidence import ArticleEvidencePolicy
from app.ingestion.service import ArticleIngestionService, NormalizedArticle
from app.ingestion.url_provider import URLExtractionError, URLExtractionProvider
from app.market_data.dependencies import get_market_data_provider
from app.market_data.provider import MarketDataProvider
from app.market_data.yfinance_provider import MarketDataProviderError
from app.schemas.analysis import AnalysisCreate, AnalysisResponse, ArticleInput
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
    forecast_provider: ForecastProvider = Depends(get_forecast_provider),
    url_extraction_provider: URLExtractionProvider = Depends(get_url_extraction_provider),
) -> AnalysisResponse:
    ticker = payload.ticker.upper().strip()
    article_inputs = [
        article
        for article in payload.articles
        if (article.text and article.text.strip()) or (article.url and article.url.strip())
    ]

    if not article_inputs:
        raise HTTPException(
            status_code=400,
            detail="At least one article with manual text or an absolute URL is required.",
        )

    asset = db.scalar(select(Asset).where(Asset.symbol == ticker))
    if asset is None:
        asset = Asset(symbol=ticker, asset_type="equity", currency="USD")
        db.add(asset)
        db.flush()

    input_mode = _input_mode(article_inputs)
    analysis = Analysis(
        asset_id=asset.id,
        status="running",
        primary_horizon=payload.primary_horizon,
        input_mode=input_mode,
        limitations=[
            "Research-only output; not financial advice.",
            "URL extraction quality varies by publisher and page structure.",
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

    market_quote = MarketQuote(
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
    db.add(market_quote)

    ingestion = ArticleIngestionService()
    artifacts = ArtifactStore(settings.artifact_root)
    evidence_policy = ArticleEvidencePolicy()
    seen_hashes: set[str] = set()
    included_sentiment_labels: list[str] = []
    included_sentiment_scores: list[Decimal] = []
    article_count = 0
    included_article_count = 0

    for article_input in article_inputs:
        try:
            normalized, input_type, raw_artifact_path, extracted_artifact_path = _prepare_article(
                article_input=article_input,
                ingestion=ingestion,
                artifacts=artifacts,
                url_extraction_provider=url_extraction_provider,
            )
        except URLExtractionError as exc:
            analysis.status = "failed"
            analysis.error_message = str(exc)
            db.commit()
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        article = Article(
            asset_id=asset.id,
            title=normalized.title,
            source=normalized.source,
            url=normalized.url,
            input_type=input_type,
            raw_artifact_path=raw_artifact_path,
            extracted_text_artifact_path=extracted_artifact_path,
            content_hash=normalized.content_hash,
            language="en",
            word_count=len(normalized.text.split()),
            retrieved_at=utc_now(),
        )
        db.add(article)
        db.flush()
        evidence_decision = evidence_policy.decide(normalized, ticker, seen_hashes)
        seen_hashes.add(normalized.content_hash)
        db.add(
            AnalysisArticle(
                analysis_id=analysis.id,
                article_id=article.id,
                relevance_score=evidence_decision.relevance_score,
                duplicate_group_id=evidence_decision.duplicate_group_id,
                included_in_forecast=evidence_decision.included_in_forecast,
                exclusion_reason=evidence_decision.exclusion_reason,
            )
        )
        sentiment = sentiment_provider.score_article(normalized.text, ticker)
        sentiment_score = Decimal(str(sentiment.score))
        article_count += 1
        if evidence_decision.included_in_forecast:
            included_sentiment_labels.append(sentiment.label)
            included_sentiment_scores.append(sentiment_score)
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

    sentiment_aggregate = _build_sentiment_aggregate(
        analysis_id=analysis.id,
        article_count=article_count,
        included_labels=included_sentiment_labels,
        included_scores=included_sentiment_scores,
        included_article_count=included_article_count,
    )
    db.add(sentiment_aggregate)

    for forecast in forecast_provider.generate_forecasts(
        ForecastInput(
            ticker=ticker,
            quote_provider=market_quote.provider,
            current_price=market_quote.price,
            previous_close=market_quote.previous_close,
            quote_time=market_quote.quote_time,
            sentiment_score=sentiment_aggregate.aggregate_score,
            agreement_score=sentiment_aggregate.agreement_score,
            evidence_strength_score=sentiment_aggregate.evidence_strength_score,
            article_count=sentiment_aggregate.article_count,
            included_article_count=sentiment_aggregate.included_article_count,
        )
    ):
        db.add(
            ForecastRun(
                analysis_id=analysis.id,
                asset_id=asset.id,
                horizon=forecast.horizon,
                provider=forecast.provider,
                model_name=forecast.model_name,
                model_version=forecast.model_version,
                predicted_direction=forecast.predicted_direction,
                predicted_percent_change=_float_to_decimal(forecast.predicted_percent_change),
                confidence_score=Decimal(str(forecast.confidence)),
                baseline_direction=forecast.baseline_direction,
                baseline_percent_change=_float_to_decimal(forecast.baseline_percent_change),
                feature_snapshot=forecast.feature_snapshot,
                top_factors=forecast.top_factors,
                limitations=forecast.limitations,
                target_start_price=forecast.target_start_price,
                target_start_time=forecast.target_start_time,
                target_end_time=forecast.target_end_time,
            )
        )

    analysis.status = "completed"
    analysis.completed_at = utc_now()
    db.commit()

    persisted = _get_analysis(db, analysis.id)
    return _to_response(persisted, "Analysis created with persisted article evidence.")


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
        .options(selectinload(Analysis.analysis_articles))
        .options(selectinload(Analysis.sentiment_runs))
        .options(selectinload(Analysis.sentiment_aggregate))
        .options(selectinload(Analysis.forecast_runs))
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
            selectinload(Analysis.analysis_articles),
            selectinload(Analysis.sentiment_runs),
            selectinload(Analysis.sentiment_aggregate),
            selectinload(Analysis.forecast_runs),
        )
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis


def _to_response(analysis: Analysis, message: str) -> AnalysisResponse:
    market_quote = max(analysis.market_quotes, key=lambda quote: quote.retrieved_at, default=None)
    article_metadata = {join.article_id: join for join in analysis.analysis_articles}

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
                "relevance_score": _decimal_to_str(
                    article_metadata[article.id].relevance_score
                )
                if article.id in article_metadata
                else None,
                "duplicate_group_id": article_metadata[article.id].duplicate_group_id
                if article.id in article_metadata
                else None,
                "included_in_forecast": article_metadata[article.id].included_in_forecast
                if article.id in article_metadata
                else True,
                "exclusion_reason": article_metadata[article.id].exclusion_reason
                if article.id in article_metadata
                else None,
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
        forecast_runs=[
            {
                "id": run.id,
                "horizon": run.horizon,
                "provider": run.provider,
                "model_name": run.model_name,
                "model_version": run.model_version,
                "predicted_direction": run.predicted_direction,
                "predicted_percent_change": _decimal_to_str(run.predicted_percent_change),
                "confidence_score": _decimal_to_str(run.confidence_score) or "0",
                "baseline_direction": run.baseline_direction,
                "baseline_percent_change": _decimal_to_str(run.baseline_percent_change),
                "feature_snapshot": run.feature_snapshot or {},
                "top_factors": run.top_factors or [],
                "limitations": run.limitations or [],
                "target_start_price": _decimal_to_str(run.target_start_price),
                "target_start_time": _datetime_to_str(run.target_start_time),
                "target_end_time": _datetime_to_str(run.target_end_time),
            }
            for run in sorted(analysis.forecast_runs, key=lambda item: item.horizon)
        ],
    )


def _input_mode(article_inputs: list[ArticleInput]) -> str:
    has_text = any(article.text and article.text.strip() for article in article_inputs)
    has_url = any(article.url and article.url.strip() and not article.text for article in article_inputs)
    if has_text and has_url:
        return "mixed"
    if has_url:
        return "url"
    return "manual_text"


def _prepare_article(
    article_input: ArticleInput,
    ingestion: ArticleIngestionService,
    artifacts: ArtifactStore,
    url_extraction_provider: URLExtractionProvider,
) -> tuple[NormalizedArticle, str, str, str]:
    if article_input.text and article_input.text.strip():
        normalized = ingestion.normalize_text(
            article_input.text,
            title=article_input.title,
            source=article_input.source,
            url=article_input.url,
        )
        artifact_path = artifacts.write_article_text(normalized.content_hash, normalized.text)
        return normalized, "manual_text", artifact_path, artifact_path

    if article_input.url is None:
        raise URLExtractionError("Article URL is required when manual text is absent.")

    extracted = url_extraction_provider.extract(article_input.url)
    normalized = ingestion.normalize_text(
        extracted.text,
        title=article_input.title or extracted.title,
        source=article_input.source or extracted.source,
        url=extracted.final_url,
    )
    raw_artifact_path = artifacts.write_article_html(normalized.content_hash, extracted.raw_html)
    extracted_artifact_path = artifacts.write_article_text(normalized.content_hash, normalized.text)
    return normalized, "url", raw_artifact_path, extracted_artifact_path


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


def _float_to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _build_sentiment_aggregate(
    analysis_id: str,
    article_count: int,
    included_labels: list[str],
    included_scores: list[Decimal],
    included_article_count: int,
) -> SentimentAggregate:
    positive_count = included_labels.count("positive")
    neutral_count = included_labels.count("neutral")
    negative_count = included_labels.count("negative")
    mixed_count = included_labels.count("mixed")
    aggregate_score = sum(included_scores, Decimal("0")) / Decimal(max(len(included_scores), 1))
    dominant_count = max(positive_count, neutral_count, negative_count, mixed_count, 0)
    agreement_score = Decimal(str(dominant_count / max(included_article_count, 1)))
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
