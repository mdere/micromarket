import argparse
from pathlib import Path

from app.db.session import SessionLocal
from app.ingestion.entity_registry import (
    DEFAULT_SEED_PATH,
    import_entity_seed_definitions,
    load_sp500_wikipedia_snapshot,
    load_seed_file,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import reviewed entity seed definitions.")
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SEED_PATH),
        help="Path to a reviewed entity seed JSON file.",
    )
    parser.add_argument(
        "--sp500-wikipedia",
        action="store_true",
        help="Fetch and import the current Wikipedia S&P 500 component table.",
    )
    args = parser.parse_args()
    if args.sp500_wikipedia:
        records = load_sp500_wikipedia_snapshot()
        source_label = "Wikipedia S&P 500 component table"
    else:
        records = load_seed_file(Path(args.source))
        source_label = args.source
    db = SessionLocal()
    try:
        imported = import_entity_seed_definitions(db, records)
        db.commit()
    finally:
        db.close()
    print(f"Imported {imported} entity seed definitions from {source_label}")


if __name__ == "__main__":
    main()
