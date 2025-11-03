"""Add attribution url column to organisation table

Revision ID: 0070
Revises: 0069
Create Date: 2025-07-29 14:12:10.294378

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0070"
down_revision = "0069"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organisation", sa.Column("attribution_url", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_column("organisation", "attribution_url")
    # ### end Alembic commands ###
