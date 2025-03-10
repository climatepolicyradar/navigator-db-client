"""Add auto-increment to geography ID

Revision ID: 0061
Revises: 0060
Create Date: 2025-03-10 14:58:54.023942

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0061"
down_revision = "0060"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_geography__display_value", "geography", type_="unique")


def downgrade():
    op.create_unique_constraint(
        "uq_geography__display_value", "geography", ["display_value"]
    )
