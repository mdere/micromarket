from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.ingestion.entities import DeterministicEntityExtractor
from app.ingestion.entity_registry import (
    import_entity_seed_definitions,
    load_reviewed_entity_definitions,
    load_seed_file,
    parse_sp500_wikipedia_html,
)


def test_entity_seed_import_loads_reviewed_definitions() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    db = testing_session()

    try:
        imported = import_entity_seed_definitions(db, load_seed_file())
        db.commit()

        assert imported > 0
        definitions = load_reviewed_entity_definitions(db)
        by_name = {definition.name: definition for definition in definitions}
        assert by_name["Samsung"].symbol == "SSNLF"
        assert by_name["Coca-Cola"].symbol == "KO"
        assert by_name["Disney"].symbol == "DIS"

        extractor = DeterministicEntityExtractor(definitions)
        entities = extractor.extract(
            "Coke expanded retail distribution while Disney reported stronger parks demand.",
            "SPY",
        )
        by_entity_name = {entity.name: entity for entity in entities}
        assert by_entity_name["Coca-Cola"].symbol == "KO"
        assert by_entity_name["Disney"].symbol == "DIS"
    finally:
        db.close()


def test_parse_sp500_wikipedia_html_builds_seed_records() -> None:
    html = """
    <html>
      <body>
        <table>
          <tr><th>Symbol</th><th>Security</th><th>GICS Sector</th></tr>
          <tr><td>KO</td><td>Coca-Cola Company</td><td>Consumer Staples</td></tr>
          <tr><td>DIS</td><td>Walt Disney Company</td><td>Communication Services</td></tr>
        </table>
      </body>
    </html>
    """

    records = parse_sp500_wikipedia_html(html, source_date=date(2026, 5, 1))

    assert records == [
        {
            "entity_type": "asset",
            "name": "Coca-Cola Company",
            "canonical_name": "coca-cola",
            "symbol": "KO",
            "aliases": ["Coca-Cola", "Coca-Cola Company", "KO"],
            "relationship_type": "mentioned_with",
            "confidence": 0.76,
            "source": "sp500_wikipedia_snapshot",
            "source_date": "2026-05-01",
            "reviewed_at": "2026-05-01",
            "exchange": "US",
            "sector": "Consumer Staples",
        },
        {
            "entity_type": "asset",
            "name": "Walt Disney Company",
            "canonical_name": "walt disney",
            "symbol": "DIS",
            "aliases": ["DIS", "Walt Disney", "Walt Disney Company"],
            "relationship_type": "mentioned_with",
            "confidence": 0.76,
            "source": "sp500_wikipedia_snapshot",
            "source_date": "2026-05-01",
            "reviewed_at": "2026-05-01",
            "exchange": "US",
            "sector": "Communication Services",
        },
    ]
