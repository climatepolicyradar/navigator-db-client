"""Add indexes for geo query columns

Revision ID: 0067
Revises: 0066
Create Date: 2025-04-29 17:39:15.414259

"""

from alembic import op

revision = "0067"
down_revision = "0066"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_family_import_id", "family", ["import_id"], unique=True)
    op.create_index(
        "idx_family_corpus_import_id",
        "family_corpus",
        ["corpus_import_id", "family_import_id"],
    )
    op.create_index("idx_corpus_import_id", "corpus", ["import_id"], unique=True)


def downgrade():
    op.drop_index("idx_corpus_import_id", "corpus")
    op.drop_index("idx_family_corpus_import_id", "family_corpus")
    op.drop_index("idx_family_import_id", "family")
