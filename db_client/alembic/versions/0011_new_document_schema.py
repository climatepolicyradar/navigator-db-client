"""new document schema

Revision ID: 0011
Revises: 0010
Create Date: 2023-01-31 16:39:09.266079

"""

import sqlalchemy as sa
from alembic import op
from alembic.op import execute

# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "physical_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("md5_sum", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_physical_document")),
    )
    op.create_table(
        "physical_document_language",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["physical_document.id"],
            name=op.f("fk_physical_document_language__document_id__physical_document"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["language_id"],
            ["language.id"],
            name=op.f("fk_physical_document_language__language_id__language"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_physical_document_language")),
    )
    # ### end Alembic commands ###

    # Now do the column type migration
    execute("alter table language alter column id type integer")
    execute("alter table passage alter column language_id type integer")
    execute("alter sequence language_id_seq as integer")


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("physical_document_language")
    op.drop_table("physical_document")
    # ### end Alembic commands ###

    # NOTE: There is no downgrade for the column type migration
