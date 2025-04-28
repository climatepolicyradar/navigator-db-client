"""Add import id to slug table, so generated slugs can also be associated with collections

Revision ID: 0066
Revises: 0065
Create Date: 2025-04-24 16:11:15.414259

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0066"
down_revision = "0065"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("slug", sa.Column("collection_import_id", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_slug__collection_import_id__collection"),
        "slug",
        "collection",
        ["collection_import_id"],
        ["import_id"],
    )
    # Drop the existing CheckConstraint if it exists
    op.drop_constraint("must_reference_exactly_one_entity", "slug", type_="check")

    # Add the updated CheckConstraint
    op.create_check_constraint(
        "must_reference_exactly_one_entity",  # New constraint name
        "slug",  # Table name
        "num_nonnulls(family_import_id, family_document_import_id, collection_import_id) = 1",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk_slug__collection_import_id__collection"), "slug", type_="foreignkey"
    )
    op.drop_column("slug", "collection_import_id")
    # Revert the CheckConstraint change during downgrade
    op.drop_constraint("must_reference_exactly_one_entity", "slug", type_="check")

    # Add the original CheckConstraint back
    op.create_check_constraint(
        "must_reference_exactly_one_entity",
        "slug",
        "num_nonnulls(family_import_id, family_document_import_id) = 1",
    )
