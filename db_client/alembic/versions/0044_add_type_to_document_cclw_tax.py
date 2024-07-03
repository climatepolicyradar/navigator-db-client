"""Add type to _document CCLW taxonomy.

Revision ID: 0044
Revises: 0043
Create Date: 2024-07-02 15:34:00.140151

"""

from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_utils import read_taxonomy_values
from db_client.utils import get_library_path

# revision identifiers, used by Alembic.
revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None

Base = automap_base()

LAWS_AND_POLICIES = "Laws and Policies"

TAXONOMY_DATA = [
    {
        "key": "topic",
        "filename": f"{get_library_path()}/alembic/versions/data/0044/topic_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "sector",
        "filename": f"{get_library_path()}/alembic/versions/data/0044/sector_data.json",
        "file_key_path": "node.name",
        "allow_blanks": True,
    },
    {
        "key": "keyword",
        "filename": f"{get_library_path()}/alembic/versions/data/0044/keyword_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "instrument",
        "filename": f"{get_library_path()}/alembic/versions/data/0044/instrument_data.json",
        "file_key_path": "node.name",
        "allow_blanks": True,
    },
    {
        "key": "hazard",
        "filename": f"{get_library_path()}/alembic/versions/data/0044/hazard_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "framework",
        "filename": f"{get_library_path()}/alembic/versions/data/0044/framework_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "event_type",
        "filename": f"{get_library_path()}/alembic/versions/data/0044/event_type_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "_document",
        "taxonomy": [
            {
                "key": "role",
                "filename": f"{get_library_path()}/alembic/versions/data/0044/document_role_data.json",
                "file_key_path": "name",
                "allow_blanks": False,
            },
            {
                "key": "type",
                "filename": f"{get_library_path()}/alembic/versions/data/0044/document_type_data.json",
                "file_key_path": "name",
                "allow_blanks": False,
            },
        ],
    },
]


def get_cclw_taxonomy():
    taxonomy = read_taxonomy_values(TAXONOMY_DATA)

    # Remove unwanted values for new taxonomy
    if "sector" in taxonomy:
        sectors = taxonomy["sector"]["allowed_values"]
        if "Transportation" in sectors:
            taxonomy["sector"]["allowed_values"] = [
                s for s in sectors if s != "Transportation"
            ]

    return taxonomy


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
        session,
        CorpusType,
        LAWS_AND_POLICIES,
        get_cclw_taxonomy(),
    )


def downgrade():
    # There is no way back
    pass
