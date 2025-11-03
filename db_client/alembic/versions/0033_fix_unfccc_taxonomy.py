"""Fix the UNFCCC taxonomy

Revision ID: 0033
Revises: 0032
Create Date: 2024-03-02 sometime after breakfast

"""

from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_utils import read_taxonomy_values

# revision identifiers, used by Alembic.
revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

Base = automap_base()

INTL_AGREEMENTS = "Intl. agreements"

TAXONOMY_DATA = [
    {
        "key": "author_type",
        "allow_blanks": False,
        "allowed_values": ["Party", "Non-Party"],
    },
    {
        "key": "author",
        "allow_blanks": False,
        "allow_any": True,
        "allowed_values": [],
    },
]


def get_unf3c_taxonomy():
    return read_taxonomy_values(TAXONOMY_DATA)


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
