"""Drop FamilyDocumentRole table.

Revision ID: 0046
Revises: 0045
Create Date: 2024-07-10 10:01:33.721363

"""

from alembic import op

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "fk_family_document__document_role__family_document_role",
        "family_document",
        type_="foreignkey",
    )
    op.drop_table("family_document_role")
    op.drop_column("family_document", "document_role")
    # ### end Alembic commands ###


def downgrade():
    pass  # No way back