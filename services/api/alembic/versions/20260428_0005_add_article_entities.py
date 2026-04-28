"""add article entities and asset relationships

Revision ID: 20260428_0005
Revises: 20260428_0004
Create Date: 2026-04-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260428_0005"
down_revision: str | None = "20260428_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_type", "canonical_name", name="uq_entities_type_canonical"),
    )
    op.create_index(op.f("ix_entities_canonical_name"), "entities", ["canonical_name"], unique=False)
    op.create_index(op.f("ix_entities_symbol"), "entities", ["symbol"], unique=False)

    op.create_table(
        "article_entities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("article_id", sa.String(length=36), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("evidence_snippets", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "article_id", "entity_id", "provider", name="uq_article_entities_provider"
        ),
    )
    op.create_index(
        op.f("ix_article_entities_article_id"),
        "article_entities",
        ["article_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_entities_entity_id"),
        "article_entities",
        ["entity_id"],
        unique=False,
    )

    op.create_table(
        "asset_relationships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("related_entity_id", sa.String(length=36), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["related_entity_id"], ["entities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id",
            "related_entity_id",
            "relationship_type",
            name="uq_asset_relationships_type",
        ),
    )
    op.create_index(
        op.f("ix_asset_relationships_asset_id"),
        "asset_relationships",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_relationships_related_entity_id"),
        "asset_relationships",
        ["related_entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_asset_relationships_related_entity_id"), table_name="asset_relationships"
    )
    op.drop_index(op.f("ix_asset_relationships_asset_id"), table_name="asset_relationships")
    op.drop_table("asset_relationships")
    op.drop_index(op.f("ix_article_entities_entity_id"), table_name="article_entities")
    op.drop_index(op.f("ix_article_entities_article_id"), table_name="article_entities")
    op.drop_table("article_entities")
    op.drop_index(op.f("ix_entities_symbol"), table_name="entities")
    op.drop_index(op.f("ix_entities_canonical_name"), table_name="entities")
    op.drop_table("entities")
