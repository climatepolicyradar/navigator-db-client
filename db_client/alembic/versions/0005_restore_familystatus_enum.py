"""Restore the orphaned familystatus enum type lost when history was flattened

Old migration 0013 created the `familystatus` enum for family.family_status, and old
migration 0017 dropped that column but left the type behind. The flattened baseline
(0001) did not recreate the type, so databases built from it differ from those
migrated through the old chain. No column uses the type; it is restored only so that
both kinds of database have the same schema.

Postgres has no CREATE TYPE IF NOT EXISTS, so the creation is guarded: databases
that were created through the old chain (and re-stamped) already have the type.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-05

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'familystatus') THEN
                CREATE TYPE familystatus AS ENUM ('CREATED', 'PUBLISHED', 'DELETED');
            END IF;
        END
        $$
        """
    )


def downgrade():
    op.execute("DROP TYPE IF EXISTS familystatus")
