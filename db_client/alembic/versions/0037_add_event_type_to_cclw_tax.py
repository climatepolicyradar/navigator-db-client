"""Add event_type to CCLW taxonomy.

Revision ID: 0037
Revises: 0036
Create Date: 2024-06-26 08:51:00.140151

"""

from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_cclw import get_cclw_taxonomy

# revision identifiers, used by Alembic.
revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None

Base = automap_base()

LAWS_AND_POLICIES = "Laws and Policies"


def update_corpus_type_taxonomy(session, CorpusType, name, new_taxonomy):
    # Get the exiting corpus type for Intl. agreements
    cclw_ct = session.query(CorpusType).filter(CorpusType.name == name).one()
    # update
    cclw_ct.valid_metadata = new_taxonomy
    # add
    session.add(cclw_ct)
    session.commit()


def upgrade():
    bind = op.get_bind()
    session: Session = Session(bind=bind)

    Base.prepare(autoload_with=bind)
    CorpusType = Base.classes.corpus_type
    update_corpus_type_taxonomy(
        session, CorpusType, LAWS_AND_POLICIES, get_cclw_taxonomy()
    )


def downgrade():
    # There is no way back
    pass
