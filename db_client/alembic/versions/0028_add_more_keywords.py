"""
Add more keywords for CCLW metadata

Revision ID: 0028
Revises: 0027
Create Date: 2024-02-26 12:00:00

"""

import json
from string import Template
from typing import Callable, Union, cast

import sqlalchemy as sa
from alembic import op
from slugify import slugify
from sqlalchemy import update
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_utils import read_taxonomy_values
from db_client.data_migrations.utils import (
    has_rows,
    load_list,
    load_list_idempotent,
    load_tree,
)
from db_client.models import ORGANISATION_CCLW, ORGANISATION_UNFCCC
from db_client.models.dfce.family import (
    FamilyDocumentRole,
    FamilyDocumentType,
    FamilyEventType,
    Variant,
)
from db_client.models.dfce.geography import (
    CPR_DEFINED_GEOS,
    GEO_OTHER,
    Geography,
    GeoStatistics,
)
from db_client.models.document.physical_document import Language
from db_client.models.organisation.counters import EntityCounter
from db_client.utils import get_library_path

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


UNFCCC_TAXONOMY_DATA = [
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


CCLW_TAXONOMY_DATA = [
    {
        "key": "topic",
        "filename": f"{get_library_path()}/data_migrations/data/cclw/topic_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "sector",
        "filename": f"{get_library_path()}/data_migrations/data/cclw/sector_data.json",
        "file_key_path": "node.name",
        "allow_blanks": True,
    },
    {
        "key": "keyword",
        "filename": f"{get_library_path()}/data_migrations/data/cclw/keyword_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "instrument",
        "filename": f"{get_library_path()}/data_migrations/data/cclw/instrument_data.json",
        "file_key_path": "node.name",
        "allow_blanks": True,
    },
    {
        "key": "hazard",
        "filename": f"{get_library_path()}/data_migrations/data/cclw/hazard_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "framework",
        "filename": f"{get_library_path()}/data_migrations/data/cclw/framework_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
]


def _get_unf3c_taxonomy():
    return read_taxonomy_values(UNFCCC_TAXONOMY_DATA)


def _get_cclw_taxonomy():
    taxonomy = read_taxonomy_values(CCLW_TAXONOMY_DATA)

    # Remove unwanted values for new taxonomy
    if "sector" in taxonomy:
        sectors = taxonomy["sector"]["allowed_values"]
        if "Transportation" in sectors:
            taxonomy["sector"]["allowed_values"] = [
                s for s in sectors if s != "Transportation"
            ]

    return taxonomy


def _add_geo_slugs(geo_tree: list[dict[str, dict]]):
    for entry in geo_tree:
        data = entry["node"]
        data["slug"] = slugify(data["display_value"], separator="-")

        child_nodes = cast(list[dict[str, dict]], entry["children"])
        if child_nodes:
            _add_geo_slugs(child_nodes)


def remove_old_international_geo(db: Session) -> None:
    db_international = (
        db.query(Geography).filter(Geography.value == "INT").one_or_none()
    )
    if db_international is not None:
        db_stats = (
            db.query(GeoStatistics)
            .filter(GeoStatistics.geography_id == db_international.id)
            .one_or_none()
        )
        if db_stats is not None:
            db.delete(db_stats)
            db.flush()
        db.delete(db_international)
        db.flush()


def to_float(value: str) -> Union[float, None]:
    first_str = value.split(" ")[0]
    retval = None
    try:
        retval = float(first_str)
    except ValueError:
        print(f"Unparsable for float: {first_str}")
    return retval


def _apply_geo_statistics_updates(db: Session) -> None:
    with open(
        f"{get_library_path()}/data_migrations/data/geo_stats_updates.json"
    ) as geo_stats_file:
        geo_stats_data = json.load(geo_stats_file)
        for geo_stat in geo_stats_data:
            geography_id = (
                db.query(Geography.id)
                .filter_by(value=geo_stat["iso"], display_value=geo_stat["name"])
                .scalar()
            )
            geo_stats_id = (
                db.query(GeoStatistics.id).filter_by(geography_id=geography_id).scalar()
            )
            args = {**geo_stat}
            args["geography_id"] = geography_id
            del args["iso"]
            result = db.execute(
                update(GeoStatistics)
                .values(**args)
                .where(GeoStatistics.geography_id == geography_id)
            )

            if result.rowcount == 0:  # type: ignore
                raise ValueError(
                    f"In geo_stats id: {geo_stats_id} for geo: {geo_stat['name']}"
                )


def _populate_initial_geo_statistics(db: Session) -> None:
    """Populates the geo_statistics table with pre-defined data."""

    if has_rows(db, GeoStatistics):
        return

    # Load geo_stats data from structured data file
    with open(
        f"{get_library_path()}/data_migrations/data/geo_stats_data.json"
    ) as geo_stats_file:
        geo_stats_data = json.load(geo_stats_file)
        for geo_stat in geo_stats_data:
            geography_id = (
                db.query(Geography.id)
                .filter_by(value=geo_stat["iso"], display_value=geo_stat["name"])
                .scalar()
            )
            args = {**geo_stat}
            args["geography_id"] = geography_id
            del args["iso"]
            db.add(GeoStatistics(**args))


def _populate_counters(db: Session):
    n_rows = db.query(EntityCounter).count()
    if n_rows == 0:
        db.add(
            EntityCounter(
                prefix=ORGANISATION_CCLW, description="Counter for CCLW entities"
            )
        )
        db.add(
            EntityCounter(
                prefix=ORGANISATION_UNFCCC, description="Counter for UNFCCC entities"
            )
        )
        db.commit()


def _populate_language(db: Session) -> None:
    """Populates the langauge table with pre-defined data."""

    if has_rows(db, Language):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/language_data.json"
    ) as language_file:
        language_data = json.load(language_file)
        load_list(db, Language, language_data)


def _populate_document_type(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, FamilyDocumentType):
        return

    # This is no longer fixed but additive,
    # meaning we will add anything here that is not present in the table

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/document_type_data.json"
    ) as submission_type_file:
        document_type_data = json.load(submission_type_file)
        load_list_idempotent(
            db, FamilyDocumentType, FamilyDocumentType.name, "name", document_type_data
        )

    with open(
        f"{get_library_path()}/data_migrations/data/unf3c/submission_type_data.json"
    ) as submission_type_file:
        submission_type_data = json.load(submission_type_file)
        document_type_data = [
            {"name": e["name"], "description": e["name"]} for e in submission_type_data
        ]
        load_list_idempotent(
            db, FamilyDocumentType, FamilyDocumentType.name, "name", document_type_data
        )


def _populate_document_role(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, FamilyDocumentRole):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/document_role_data.json"
    ) as document_role_file:
        document_role_data = json.load(document_role_file)
        load_list(db, FamilyDocumentRole, document_role_data)


def _populate_document_variant(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, Variant):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/document_variant_data.json"
    ) as document_variant_file:
        document_variant_data = json.load(document_variant_file)
        load_list(db, Variant, document_variant_data)


def _populate_event_type(db: Session) -> None:
    """Populates the family_event_type table with pre-defined data."""

    if has_rows(db, FamilyEventType):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/event_type_data.json"
    ) as event_type_file:
        event_type_data = json.load(event_type_file)
        load_list(db, FamilyEventType, event_type_data)


def _populate_geography(db: Session) -> None:
    """Populates the geography table with pre-defined data."""

    geo_populated = has_rows(db, Geography)
    if geo_populated:
        return

    # First ensure our defined entries are present
    remove_old_international_geo(db)

    # Add the Other region
    other = db.query(Geography).filter(Geography.value == GEO_OTHER).one_or_none()
    if other is None:
        other = Geography(
            display_value=GEO_OTHER,
            slug=slugify(GEO_OTHER),
            value=GEO_OTHER,
            type="ISO-3166 CPR Extension",
        )
        db.add(other)
        db.flush()

    # Add the CPR geo definitions in Other
    for value, description in CPR_DEFINED_GEOS.items():
        db_geo = db.query(Geography).filter(Geography.value == value).one_or_none()
        if db_geo is None:
            db.add(
                Geography(
                    display_value=description,
                    slug=slugify(value),
                    value=value,
                    type="ISO-3166 CPR Extension",
                    parent_id=other.id,
                )
            )

    if geo_populated:
        return

    with open(
        f"{get_library_path()}/data_migrations/data/geography_data.json"
    ) as geo_data_file:
        geo_data = json.loads(geo_data_file.read())
        _add_geo_slugs(geo_data)
        load_tree(db, Geography, geo_data)


def _populate_geo_statistics(db: Session) -> None:
    _populate_initial_geo_statistics(db)
    db.flush()
    _apply_geo_statistics_updates(db)


def _populate_org_taxonomy(
    session: Session,
    org_name: str,
    org_type: str,
    description: str,
    fn_get_taxonomy: Callable,
) -> None:
    """Populates the taxonomy from the data."""

    # First the org
    Org = Base.classes.organisation
    org = session.query(Org).filter(Org.name == org_name).one_or_none()
    if org is None:
        org = Org(name=org_name, description=description, organisation_type=org_type)
        session.add(org)
        session.flush()
        session.commit()

    MetaOrg = Base.metadata.tables["metadata_organisation"]
    metadata_org = sa.select([MetaOrg]).where(MetaOrg.c.organisation_id == org.id)
    metadata_org = session.execute(metadata_org).fetchone()

    if metadata_org is None:
        # Now add the taxonomy
        MetaTax = Base.classes.metadata_taxonomy
        tax = MetaTax(
            description=f"{org_name} loaded values",
            valid_metadata=fn_get_taxonomy(),
        )
        session.add(tax)
        session.flush()

        # Finally the link between the org and the taxonomy.
        stmt = sa.sql.insert(MetaOrg).values(taxonomy_id=tax.id, organisation_id=org.id)
        session.execute(stmt)
        session.flush()
        session.commit()


def _populate_taxonomy(session: Session) -> None:
    Org = Base.classes.organisation
    if has_rows(session, Org):
        return

    _populate_org_taxonomy(
        session,
        org_name=ORGANISATION_CCLW,
        org_type="Academic",
        description="Climate Change Laws of the World",
        fn_get_taxonomy=_get_cclw_taxonomy,
    )
    _populate_org_taxonomy(
        session,
        org_name=ORGANISATION_UNFCCC,
        org_type="UN",
        description="United Nations Framework Convention on Climate Change",
        fn_get_taxonomy=_get_unf3c_taxonomy,
    )


def get_cclw_id_and_keywords(session):
    Org = Base.classes.organisation
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
    Base.prepare(autoload_with=bind)

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
