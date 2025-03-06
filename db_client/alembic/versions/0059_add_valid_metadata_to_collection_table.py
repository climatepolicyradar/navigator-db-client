"""Add valid_metadata column to the collection table

Revision ID: 0059
Revises: 0058
Create Date: 2025-03-06 12:23:22.657834

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "collection", sa.Column("valid_metadata", postgresql.JSONB, nullable=True)
    )
    op.execute(
        sa.text(
            "UPDATE collection "
            "SET valid_metadata = '{}' "
            "WHERE valid_metadata IS NULL"
        )
    )
    op.alter_column(
        "collection", "valid_metadata", existing_type=postgresql.JSONB, nullable=False
    )


def downgrade():
    op.drop_column("collection", "valid_metadata")
