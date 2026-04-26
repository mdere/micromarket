from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.models import Base
from app.db.session import get_db
from app.main import app


def test_create_and_get_analysis(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    def override_settings() -> Settings:
        return Settings(ARTIFACT_ROOT=str(tmp_path))

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = override_settings

    try:
        client = TestClient(app)
        response = client.post(
            "/analyses",
            json={
                "ticker": "spy",
                "articles": [
                    {
                        "title": "SPY earnings sentiment",
                        "source": "manual note",
                        "text": "SPY saw improving breadth and resilient demand across large caps.",
                    }
                ],
            },
        )

        assert response.status_code == 201
        created = response.json()
        assert created["ticker"] == "SPY"
        assert created["status"] == "completed"
        assert created["primary_horizon"] == "3_trading_days"
        assert created["articles"][0]["word_count"] == 10
        artifact_path = created["articles"][0]["raw_artifact_path"]
        assert artifact_path is not None
        assert "SPY saw improving breadth" in open(artifact_path, encoding="utf-8").read()

        fetched = client.get(f"/analyses/{created['id']}")

        assert fetched.status_code == 200
        assert fetched.json()["id"] == created["id"]
        assert fetched.json()["articles"][0]["content_hash"] == created["articles"][0]["content_hash"]
    finally:
        app.dependency_overrides.clear()


def test_create_analysis_requires_manual_text(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    def override_settings() -> Settings:
        return Settings(ARTIFACT_ROOT=str(tmp_path))

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = override_settings

    try:
        client = TestClient(app)
        response = client.post("/analyses", json={"ticker": "AAPL", "articles": []})

        assert response.status_code == 400
        assert "manual article" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
