"""Add attribution url column to corpus table

Revision ID: 0071
Revises: 0070
Create Date: 2025-08-06 14:12:10.294378

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0071"
down_revision = "0070"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("corpus", sa.Column("attribution_url", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    op.drop_column("corpus", "attribution_url")
    # ### end Alembic commands ###
