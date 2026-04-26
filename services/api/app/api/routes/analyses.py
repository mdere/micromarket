from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.db.models import Analysis, AnalysisArticle, Article, Asset, utc_now
from app.db.session import get_db
from app.ingestion.service import ArticleIngestionService
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.storage import ArtifactStore

router = APIRouter()


@router.post("", response_model=AnalysisResponse, status_code=201)
def create_analysis(
    payload: AnalysisCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
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

    ingestion = ArticleIngestionService()
    artifacts = ArtifactStore(settings.artifact_root)

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
        .order_by(Analysis.created_at.desc())
        .limit(25)
    ).all()
    return [_to_response(analysis, "Analysis retrieved.") for analysis in analyses]


def _get_analysis(db: Session, analysis_id: str) -> Analysis:
    analysis = db.scalar(
        select(Analysis)
        .where(Analysis.id == analysis_id)
        .options(selectinload(Analysis.asset), selectinload(Analysis.articles))
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis


def _to_response(analysis: Analysis, message: str) -> AnalysisResponse:
    completed_at = analysis.completed_at
    if completed_at is not None and completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=timezone.utc)

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
    )
