import argparse
from pathlib import Path

from app.db.session import SessionLocal
from app.ingestion.entity_registry import (
    DEFAULT_SEED_PATH,
    import_entity_seed_definitions,
    load_seed_file,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import reviewed entity seed definitions.")
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SEED_PATH),
        help="Path to a reviewed entity seed JSON file.",
    )
    args = parser.parse_args()
    records = load_seed_file(Path(args.source))
    db = SessionLocal()
    try:
        imported = import_entity_seed_definitions(db, records)
        db.commit()
    finally:
        db.close()
    print(f"Imported {imported} entity seed definitions from {args.source}")


if __name__ == "__main__":
    main()
