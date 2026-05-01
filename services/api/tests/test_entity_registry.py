from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.ingestion.entities import DeterministicEntityExtractor
from app.ingestion.entity_registry import (
    import_entity_seed_definitions,
    load_reviewed_entity_definitions,
    load_seed_file,
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
