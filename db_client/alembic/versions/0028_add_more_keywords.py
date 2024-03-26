"""
Add more keywords for CCLW metadata

Revision ID: 0028
Revises: 0027
Create Date: 2024-02-26 12:00:00

"""

import json
from string import Template

from alembic import op
from data_migrations.populate_counters import _populate_counters
from data_migrations.populate_document_role import _populate_document_role
from data_migrations.populate_document_type import _populate_document_type
from data_migrations.populate_document_variant import _populate_document_variant
from data_migrations.populate_event_type import _populate_event_type
from data_migrations.populate_geo_statistics import _populate_geo_statistics
from data_migrations.populate_geography import _populate_geography
from data_migrations.populate_language import _populate_language
from data_migrations.populate_taxonomy import _populate_taxonomy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

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
    _populate_document_type(session)
    _populate_document_role(session)
    _populate_document_variant(session)
    _populate_event_type(session)
    _populate_geography(session)
    _populate_language(session)
    _populate_taxonomy(session)
    _populate_counters(session)

    session.flush()  # Geography data is used by geo-stats so flush

    _populate_geo_statistics(session)


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
