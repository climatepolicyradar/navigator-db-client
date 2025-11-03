"""Add litigation which is a new corpus type to the family category model

Revision ID: 0063
Revises: 0062
Create Date: 2025-03-17 12:37:49.987901

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0063"
down_revision = "0062"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE familycategory ADD VALUE 'LITIGATION'")


def downgrade():
    pass
