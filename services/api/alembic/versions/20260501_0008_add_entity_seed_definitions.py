"""add entity seed definitions

Revision ID: 20260501_0008
Revises: 20260430_0007
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0008"
down_revision: str | None = "20260430_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entity_seed_definitions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("source_date", sa.Date(), nullable=True),
        sa.Column("reviewed_at", sa.Date(), nullable=True),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "entity_type",
            "canonical_name",
            name="uq_entity_seed_definitions_source_canonical",
        ),
    )
    op.create_index(
        op.f("ix_entity_seed_definitions_canonical_name"),
        "entity_seed_definitions",
        ["canonical_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_entity_seed_definitions_symbol"),
        "entity_seed_definitions",
        ["symbol"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_entity_seed_definitions_symbol"), table_name="entity_seed_definitions")
    op.drop_index(
        op.f("ix_entity_seed_definitions_canonical_name"),
        table_name="entity_seed_definitions",
    )
    op.drop_table("entity_seed_definitions")
