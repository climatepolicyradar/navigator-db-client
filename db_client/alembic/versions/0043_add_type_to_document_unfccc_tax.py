"""Add type to _document UNFCCC taxonomy.

Revision ID: 0043
Revises: 0042
Create Date: 2024-07-03 10:24:00.140151

"""

from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_utils import read_taxonomy_values
from db_client.utils import get_library_path

# revision identifiers, used by Alembic.
revision = "0043"
down_revision = "0042"
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
    {
        "key": "event_type",
        "filename": f"{get_library_path()}/alembic/versions/data/0043/event_type_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "_document",
        "taxonomy": [
            {
                "key": "role",
                "filename": f"{get_library_path()}/alembic/versions/data/0043/document_role_data.json",
                "file_key_path": "name",
                "allow_blanks": False,
            },
            {
                "key": "type",
                "filename": f"{get_library_path()}/alembic/versions/data/0043/document_type_data.json",
                "file_key_path": "name",
                "allow_blanks": False,
            },
        ],
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
