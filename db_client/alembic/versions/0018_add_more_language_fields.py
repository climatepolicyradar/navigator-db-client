"""add more language fields

Revision ID: 0018
Revises: 0017
Create Date: 2023-08-02 11:27:34.457006

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ...models.document.physical_document import LanguageSource

# revision identifiers, used by Alembic.
revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None


def upgrade():
    # NOTE: Postgres requires the enum type to be created first, unfortunately
    #       this is not supported by autogenerate:
    #
    # Code taken from: https://stackoverflow.com/a/65173731
    language_source = postgresql.ENUM(LanguageSource, name="languagesource")
    language_source.create(op.get_bind(), checkfirst=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('physical_document_language', sa.Column(
        'source',
        language_source,
        server_default=(LanguageSource.MODEL.upper()),
        nullable=False)
    )
    op.add_column('physical_document_language', sa.Column(
        'visible',
        sa.Boolean(),
        server_default="0",
        nullable=False)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('physical_document_language', 'visible')
    op.drop_column('physical_document_language', 'source')
    # ### end Alembic commands ###

    # Unfortunately neither is dropping the type:
    language_source = postgresql.ENUM(LanguageSource, name="languagesource")
    language_source.drop(op.get_bind())

