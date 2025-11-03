"""Copy document type into metadata.

Revision ID: 0049
Revises: 0048
Create Date: 2024-07-17 14:01:33.721363

"""

import sqlalchemy as sa
from alembic import op

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            "UPDATE family_document "
            "SET valid_metadata = jsonb_set("
            "valid_metadata, '{type}', to_jsonb(ARRAY[document_type]), true) "
            "WHERE valid_metadata ? 'type' = false"
        )
    )


def downgrade():
    pass  # No way back
