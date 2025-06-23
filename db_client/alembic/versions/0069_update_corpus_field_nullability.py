"""Update corpus field nullability.

Revision ID: 0069
Revises: 0068
Create Date: 2025-06-23

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0069"
down_revision = "0068"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("corpus", "corpus_text", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("corpus", "description", existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    op.alter_column("corpus", "description", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("corpus", "corpus_text", existing_type=sa.VARCHAR(), nullable=True)
