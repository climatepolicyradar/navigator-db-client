"""add concepts to family

Revision ID: 0065
Revises: 0064
Create Date: 2024-03-18 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0065"
down_revision = "0064"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add concepts column to family table
    op.add_column(
        "family",
        sa.Column(
            "concepts",
            postgresql.ARRAY(postgresql.JSONB),
            nullable=True,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    # Remove concepts column from family table
    op.drop_column("family", "concepts")
