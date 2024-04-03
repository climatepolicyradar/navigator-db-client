"""Remove all references to MetadataTaxonomy, FamilyOrganisation & MetadataOrganisation

Revision ID: 0034
Revises: 0033
Create Date: 2024-04-03 10:42:16.140151

"""

from alembic import op

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE family_metadata DROP CONSTRAINT pk_family_metadata CASCADE")
    op.drop_column("family_metadata", "taxonomy_id")
    op.create_primary_key("pk_family_metadata", "family_metadata", ["family_import_id"])

    op.drop_table("metadata_organisation")
    op.drop_table("metadata_taxonomy")
    op.drop_table("family_organisation")


def downgrade():
    # There is no way back
    pass
