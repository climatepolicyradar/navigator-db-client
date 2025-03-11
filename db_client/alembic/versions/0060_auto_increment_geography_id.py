"""Add auto-increment to geography ID

Revision ID: 0060
Revises: 0059
Create Date: 2025-03-10 14:58:54.023942

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0060"
down_revision = "0059"
branch_labels = None
depends_on = None


def upgrade():
    # Create the sequence if it doesn't exist
    op.execute("CREATE SEQUENCE IF NOT EXISTS geography_id_seq")

    # Set the sequence's current value to the maximum existing ID
    op.execute(
        "SELECT setval('geography_id_seq', COALESCE((SELECT MAX(id) FROM geography), 0), true)"
    )

    # Alter the column to use the sequence
    op.execute(
        "ALTER TABLE geography ALTER COLUMN id SET DEFAULT nextval('geography_id_seq')"
    )


def downgrade():
    op.execute("ALTER TABLE geography ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS geography_id_seq")
