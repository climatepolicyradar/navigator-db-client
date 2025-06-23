"""Add corporate disclosures to familycategory enum.

Revision ID: 0070
Revises: 0069
Create Date: 2025-06-23 17:51:55.395146

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0070"
down_revision = "0069"
branch_labels = None
depends_on = None


def upgrade():
    # Add "Corporate Disclosures" to the familycategory enum
    op.execute("ALTER TYPE familycategory ADD VALUE 'CORPORATE_DISCLOSURES'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    pass
