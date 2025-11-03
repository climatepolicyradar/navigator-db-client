"""Remove event_type from valid_metadata for Intl. agreements and Laws and policies

Revision ID: 0068
Revises: 0067
Create Date: 2024-03-21

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0068"
down_revision = "0067"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove event_type field from valid_metadata JSONB column
    # This query is idempotent as it only updates "Intl. agreements" and "Laws and policies"
    # corpus types
    corpus_type = sa.table(
        "corpus_type",
        sa.column("valid_metadata", postgresql.JSONB),
        sa.column("name", sa.String),
    )

    op.execute(
        corpus_type.update()
        .where(
            sa.and_(
                corpus_type.c.valid_metadata.has_key("event_type"),
                corpus_type.c.name.in_(["Intl. agreements", "Laws and Policies"]),
            )
        )
        .values(valid_metadata=corpus_type.c.valid_metadata - "event_type")
    )


def downgrade() -> None:
    corpus_type = sa.table(
        "corpus_type",
        sa.column("valid_metadata", postgresql.JSONB),
        sa.column("name", sa.String),
    )

    # Create subquery to get event types from the existing _event subtaxonomy
    event_types = (
        sa.select(
            corpus_type.c.name,
            corpus_type.c.valid_metadata["_event"]["event_type"].label("event_type"),
        )
        .where(corpus_type.c.name.in_(["Intl. agreements", "Laws and Policies"]))
        .subquery()
    )

    # Update the corpus_type table with the event_type values from the _event subtaxonomy
    op.execute(
        corpus_type.update()
        .where(corpus_type.c.name == event_types.c.name)
        .values(
            valid_metadata=corpus_type.c.valid_metadata.concat(
                sa.func.jsonb_build_object("event_type", event_types.c.event_type)
            )
        )
    )
