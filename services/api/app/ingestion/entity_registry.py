from datetime import date
from decimal import Decimal
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EntitySeedDefinition
from app.ingestion.entities import EntityDefinition

DEFAULT_SEED_PATH = Path(__file__).with_name("entity_seed_snapshot.json")


def load_seed_file(path: Path = DEFAULT_SEED_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        records = json.load(file)
    if not isinstance(records, list):
        raise ValueError("Entity seed file must contain a list of records.")
    return records


def import_entity_seed_definitions(db: Session, records: list[dict]) -> int:
    imported = 0
    for record in records:
        aliases = [str(alias) for alias in record.get("aliases", []) if str(alias).strip()]
        if not aliases:
            raise ValueError(f"Entity seed {record.get('canonical_name')} must include aliases.")
        source = str(record.get("source") or "reviewed_seed")
        entity_type = str(record["entity_type"])
        canonical_name = str(record["canonical_name"])
        existing = db.scalar(
            select(EntitySeedDefinition)
            .where(EntitySeedDefinition.source == source)
            .where(EntitySeedDefinition.entity_type == entity_type)
            .where(EntitySeedDefinition.canonical_name == canonical_name)
        )
        if existing is None:
            existing = EntitySeedDefinition(
                source=source,
                entity_type=entity_type,
                canonical_name=canonical_name,
            )
            db.add(existing)
        existing.name = str(record["name"])
        existing.symbol = record.get("symbol")
        existing.aliases = sorted(set(aliases))
        existing.relationship_type = str(record.get("relationship_type") or "mentioned_with")
        existing.confidence_score = Decimal(str(record.get("confidence", "0.70")))
        existing.source_date = _parse_date(record.get("source_date"))
        existing.reviewed_at = _parse_date(record.get("reviewed_at"))
        existing.exchange = record.get("exchange")
        existing.sector = record.get("sector")
        existing.active = bool(record.get("active", True))
        imported += 1
    return imported


def load_reviewed_entity_definitions(db: Session) -> tuple[EntityDefinition, ...]:
    seeds = db.scalars(
        select(EntitySeedDefinition)
        .where(EntitySeedDefinition.active.is_(True))
        .order_by(EntitySeedDefinition.name)
    ).all()
    return tuple(
        EntityDefinition(
            entity_type=seed.entity_type,
            name=seed.name,
            canonical_name=seed.canonical_name,
            aliases=tuple(seed.aliases or []),
            symbol=seed.symbol,
            relationship_type=seed.relationship_type,
            confidence=float(seed.confidence_score),
        )
        for seed in seeds
    )


def _parse_date(value: object | None) -> date | None:
    if value in {None, ""}:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
