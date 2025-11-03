"""Add reports which is a new corpus type to the family category model

Revision ID: 0058
Revises: 0057
Create Date: 2025-01-21 11:56:49.987901

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE familycategory ADD VALUE 'REPORTS'")


def downgrade():
    pass
