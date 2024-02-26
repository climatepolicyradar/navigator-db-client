"""
Add more keywords for CCLW metadata

Revision ID: 0028
Revises: 0027
Create Date: 2024-02-26 12:00:00

"""
import json
from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

Base = automap_base()

# revision identifiers, used by Alembic.
revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

# See: https://linear.app/climate-policy-radar/issue/PDCT-839/keyword-options-to-add-to-keyword-field-for-cclw-data
NEW_KEYWORD_VALUES = [
    "Green Transition",
    "Green Economy",
    "Green Technology",
    "Green Investments",
    "Green Jobs",
    "Water Basin",
    "Conservation",
    "Monitoring, Reporting and Verification (MRV)",
    "Low-carbon economy",
    "Climate-related financial Risks",
]

F_UPDATE_COMMAND = """
UPDATE metadata_taxonomy 
SET valid_metadata = jsonb_set(valid_metadata, '{}', to_jsonb(E'{}'::text)) 
WHERE id = {};
"""


def get_entities(bind):
    Base.prepare(autoload_with=bind)
    Meta = Base.classes.metadata_taxonomy
    Org = Base.classes.organisation
    return Meta, Org


def get_cclw_id_and_keywords(session):
    Meta, Org  = get_entities(session.get_bind())
     # Get CCLW as an org
    cclw = session.query(Org).filter(Org.name == "CCLW").one()
    valid_metadata = cclw.metadata_taxonomy_collection[0].valid_metadata
    id = cclw.metadata_taxonomy_collection[0].id

    # Get the keywords
    return id, valid_metadata["keyword"]["allowed_values"]


def upgrade():

    bind = op.get_bind()
    session = Session(bind=bind)

    id, kw_allowed_values = get_cclw_id_and_keywords(session)

    # Add the new values
    new_values = kw_allowed_values + NEW_KEYWORD_VALUES
    clean_new_values = json.dumps(new_values).replace("'", "\\'")

    # create SQL
    sql = str.format(F_UPDATE_COMMAND, "{keyword, allowed_values}", clean_new_values, id)

    # Update new values
    op.execute(sql)


def downgrade():
    # There is no way back
    pass