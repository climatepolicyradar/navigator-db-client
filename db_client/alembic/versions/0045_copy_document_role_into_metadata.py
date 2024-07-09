"""Copy document role into metadata.

Revision ID: 0045
Revises: 0043
Create Date: 2024-07-09 14:01:33.721363

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """UPDATE family_document
SET valid_metadata = subquery.metadata
FROM (
    SELECT import_id, jsonb_build_object('role', jsonb_agg(document_role)) AS metadata
    FROM family_document
    WHERE valid_metadata IS NULL
    GROUP BY import_id
) AS subquery
WHERE family_document.import_id = subquery.import_id
AND family_document.valid_metadata IS NULL"""
    )
    op.alter_column(
        "family_document",
        "valid_metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )


def downgrade():
    pass  # No way back
