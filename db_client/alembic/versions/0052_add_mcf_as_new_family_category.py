"""add MCF as new family category

Revision ID: 0052
Revises: 0051
Create Date: 2024-08-12 14:52:42.190073

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE familycategory ADD VALUE 'MCF'")


def downgrade():
    pass
