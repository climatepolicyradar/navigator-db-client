"""
Add more keywords for CCLW metadata

Revision ID: 0028
Revises: 0027
Create Date: 2024-02-26 12:00:00

"""
import json
from string import Template

from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

from data_migrations import (
    populate_counters,
    populate_document_role,
    populate_document_type,
    populate_document_variant,
    populate_event_type,
    populate_geo_statistics,
    populate_geography,
    populate_language,
    populate_taxonomy,
)

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

F_UPDATE_COMMAND = Template(
    """
UPDATE metadata_taxonomy
SET valid_metadata = jsonb_set(valid_metadata, '{keyword, allowed_values}', to_jsonb(E'$new_values'::json))
WHERE id = $id
"""
)


def get_org(bind):
    Base.prepare(autoload_with=bind)
    Org = Base.classes.organisation
    return Org


def get_cclw_id_and_keywords(session):
    Org = get_org(session.get_bind())
    # Get CCLW as an org
    cclw = session.query(Org).filter(Org.name == "CCLW").one()
    valid_metadata = cclw.metadata_taxonomy_collection[0].valid_metadata
    id = cclw.metadata_taxonomy_collection[0].id

    # Get the keywords
    return id, valid_metadata["keyword"]["allowed_values"]


def do_old_init_data(session):
    # These functions were originally called in the `initial_data.py` script
    # which is now retired in favour of migrations like this
    populate_document_type(session)
    populate_document_role(session)
    populate_document_variant(session)
    populate_event_type(session)
    populate_geography(session)
    populate_language(session)
    populate_taxonomy(session)
    populate_counters(session)

    session.flush()  # Geography data is used by geo-stats so flush

    populate_geo_statistics(session)


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    do_old_init_data(session)

    # Now add the modification for CCLW keywords
    id, kw_allowed_values = get_cclw_id_and_keywords(session)

    # Add the new values (idempotent)
    new_values = kw_allowed_values
    for new_value in NEW_KEYWORD_VALUES:
        if new_value not in new_values:
            new_values.append(new_value)

    clean_new_values = json.dumps(new_values).replace("'", "\\'")

    # create SQL
    sql = F_UPDATE_COMMAND.substitute(new_values=clean_new_values, id=id)

    # Update new values
    op.execute(sql)


def downgrade():
    # There is no way back
    pass
