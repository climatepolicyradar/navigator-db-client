"""Add event_type to UNFCCC taxonomy.

Revision ID: 0036
Revises: 0035
Create Date: 2024-06-26 08:48:00.140151

"""

from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_unf3c import get_unf3c_taxonomy

# revision identifiers, used by Alembic.
revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None

Base = automap_base()

INTL_AGREEMENTS = "Intl. agreements"


def update_corpus_type_taxonomy(session, CorpusType, name, new_taxonomy):
    # Get the exiting corpus type for Intl. agreements
    unfccc_ct = session.query(CorpusType).filter(CorpusType.name == name).one()
    # update
    unfccc_ct.valid_metadata = new_taxonomy
    # add
    session.add(unfccc_ct)
    session.commit()


def upgrade():
    bind = op.get_bind()
    session: Session = Session(bind=bind)

    Base.prepare(autoload_with=bind)
    CorpusType = Base.classes.corpus_type
    update_corpus_type_taxonomy(
        session, CorpusType, INTL_AGREEMENTS, get_unf3c_taxonomy()
    )


def downgrade():
    # There is no way back
    pass
