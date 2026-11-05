"""Restore server defaults lost when the migration history was flattened

The pre-flatten chain (v3.9.21) set these server-side defaults, but the flattened
baseline (0001) dropped them. The ORM supplies the same values client-side, so
ORM inserts were unaffected, but raw SQL inserts that omit these columns failed
(NOT NULL violations) or stored NULL instead of an empty array.

- family.concepts                      '{}'      (old migration 0065)
- physical_document_language.source    'MODEL'   (old migration 0018)
- physical_document_language.visible   false     (old migration 0018)

entity_counter.counter is deliberately not touched: the old chain had no default
there, and the flattened default of 0 matches the model's server_default.

SET DEFAULT is idempotent, so this is a no-op for databases that still carry the
old defaults.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-05

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "family",
        "concepts",
        server_default=sa.text("'{}'::jsonb[]"),
    )
    op.alter_column(
        "physical_document_language",
        "source",
        server_default=sa.text("'MODEL'::languagesource"),
    )
    op.alter_column(
        "physical_document_language",
        "visible",
        server_default=sa.text("false"),
    )


def downgrade():
    op.alter_column("physical_document_language", "visible", server_default=None)
    op.alter_column("physical_document_language", "source", server_default=None)
    op.alter_column("family", "concepts", server_default=None)
