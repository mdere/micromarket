from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EntitySeedDefinition
from app.ingestion.entities import EntityDefinition

DEFAULT_SEED_PATH = Path(__file__).with_name("entity_seed_snapshot.json")
SP500_WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def load_seed_file(path: Path = DEFAULT_SEED_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        records = json.load(file)
    if not isinstance(records, list):
        raise ValueError("Entity seed file must contain a list of records.")
    return records


def load_sp500_wikipedia_snapshot(
    source_date: date | None = None,
    url: str = SP500_WIKIPEDIA_URL,
) -> list[dict]:
    request = Request(url, headers={"User-Agent": "micromarket local research seed importer"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    return parse_sp500_wikipedia_html(html, source_date=source_date or date.today())


def parse_sp500_wikipedia_html(html: str, source_date: date) -> list[dict]:
    parser = _WikipediaTableParser()
    parser.feed(html)
    if not parser.tables:
        raise ValueError("No HTML tables found in S&P 500 source.")
    rows, header = _find_sp500_component_table(parser.tables)
    symbol_index = header.index("symbol")
    security_index = header.index("security")
    sector_index = header.index("gics sector") if "gics sector" in header else None
    records = []
    for row in rows[1:]:
        if len(row) <= max(symbol_index, security_index):
            continue
        symbol = row[symbol_index].strip().replace(".", "-")
        name = row[security_index].strip()
        if not symbol or not name:
            continue
        sector = row[sector_index].strip() if sector_index is not None and len(row) > sector_index else None
        records.append(
            {
                "entity_type": "asset",
                "name": name,
                "canonical_name": _canonical_name(name),
                "symbol": symbol,
                "aliases": _aliases_for_company(name, symbol),
                "relationship_type": "mentioned_with",
                "confidence": 0.76,
                "source": "sp500_wikipedia_snapshot",
                "source_date": source_date.isoformat(),
                "reviewed_at": source_date.isoformat(),
                "exchange": "US",
                "sector": sector,
            }
        )
    return records


def _find_sp500_component_table(tables: list[list[list[str]]]) -> tuple[list[list[str]], list[str]]:
    for rows in tables:
        if not rows:
            continue
        header = [_normalize_cell(value) for value in rows[0]]
        if "symbol" in header and "security" in header:
            return rows, header
    raise ValueError("No S&P 500 component table found in source.")


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


def _aliases_for_company(name: str, symbol: str) -> list[str]:
    aliases = [name, symbol]
    cleaned = _strip_company_suffix(name)
    if cleaned != name:
        aliases.append(cleaned)
    return sorted(set(aliases))


def _strip_company_suffix(value: str) -> str:
    suffixes = (
        ", Inc.",
        " Inc.",
        " Corporation",
        " Corp.",
        " Company",
        " Co.",
        " plc",
        " PLC",
        " N.V.",
        " Ltd.",
        " Class A",
        " Class B",
        " Class C",
    )
    cleaned = value
    for suffix in suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return cleaned.strip()


def _canonical_name(value: str) -> str:
    return _strip_company_suffix(value).lower()


def _normalize_cell(value: str) -> str:
    return " ".join(value.lower().split())


class _WikipediaTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._in_table = False
        self._in_cell = False
        self._current_table: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and not self._in_table:
            self._in_table = True
            self._current_table = []
        elif self._in_table and tag == "tr":
            self._current_row = []
        elif self._in_table and tag in {"td", "th"}:
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if not self._in_table:
            return
        if tag in {"td", "th"} and self._in_cell:
            self._current_row.append("".join(self._current_cell).strip())
            self._in_cell = False
        elif tag == "tr" and self._current_row:
            self._current_table.append(self._current_row)
            self._current_row = []
        elif tag == "table":
            self.tables.append(self._current_table)
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell.append(data)
