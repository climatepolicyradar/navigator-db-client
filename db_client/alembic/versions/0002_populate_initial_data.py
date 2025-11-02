"""Populate initial data

Revision ID: 0002
Revises: 0001
Create Date: 2025-10-30 17:01:09.258758

"""

import json
from typing import cast

import pycountry
import sqlalchemy as sa
from alembic import op
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from pycountry.db import Country, Subdivision
from slugify import slugify
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from db_client.models.dfce.geography import CPR_DEFINED_GEOS, GEO_OTHER
from db_client.utils import get_library_path

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

Base = automap_base()


def add_organisation(session, Org, name, description, organisation_type, display_name):
    org = Org(
        name=name,
        description=description,
        organisation_type=organisation_type,
        display_name=display_name,
    )
    session.add(org)
    session.flush()
    return org


def get_organisation(session, Org, name):
    org = session.query(Org).filter(Org.name == name).one_or_none()
    return org


def add_corpus_type(session, CorpusType, name, description, valid_metadata):
    corpus_type = CorpusType(
        name=name,
        description=description,
        valid_metadata=valid_metadata,
    )
    session.add(corpus_type)
    session.flush()
    return corpus_type


def add_corpus(session, Corpus, title, description, org, corpus_type, corpus_text):
    # NOTE: we cannot use create_import_id here.. so pinch the code
    n = 0  # The fourth quad is historical
    i_value = str(1).zfill(8)
    n_value = str(n).zfill(4)
    import_id = f"{org.name}.corpus.i{i_value}.n{n_value}"
    corpus = Corpus(
        import_id=import_id,
        title=title,
        description=description,
        organisation_id=org.id,
        corpus_type=corpus_type,
        corpus_text=corpus_text,
    )
    session.add(corpus)
    session.flush()
    return corpus


def _populate_language(session: Session) -> None:
    """Populates the language table with pre-defined data."""
    if session.execute(text("select count(*) from language")).scalar() == 0:
        language_data_path = (
            f"{get_library_path()}/data_migrations/data/source/language_data.json"
        )
        with open(language_data_path) as language_file:
            language_data = json.load(language_file)
            query = text(
                "insert into language (language_code, part1_code, part2_code, name) "
                "values (:language_code, :part1_code, :part2_code, :name)"
            )
            session.execute(query, params=language_data)
    session.flush()


def _populate_document_variants(session: Session, variant):
    if session.execute(text("select count(*) from variant")).scalar() != 0:
        return

    session.execute(
        text(
            "insert into variant (variant_name, description) values (:variant_name, :description)"
        ),
        params=[
            {"variant_name": "original", "description": "Original language"},
            {"variant_name": "translation", "description": "Translation"},
        ],
    )
    session.flush()


def _populate_counters(session: Session):
    if session.execute(text("select count(*) from entity_counter")).scalar() != 0:
        return

    statement = text(
        "insert into entity_counter (prefix, description) values (:prefix, :description)"
    )
    session.execute(
        statement,
        params=[
            {"prefix": "CCLW", "description": "Counter for CCLW entities"},
            {
                "prefix": "UNFCCC",
                "description": "Counter for UNFCCC entities",
            },
        ],
    )
    session.flush()


def _populate_initial_geo_statistics(db: Session) -> None:
    """Populates the geo_statistics table with pre-defined data."""

    if db.execute(text("select count(*) from geo_statistics")).scalar() != 0:
        return

    # Load geo_stats data from structured data file
    with open(
        f"{get_library_path()}/data_migrations/data/source/geo_stats_data.json"
    ) as geo_stats_file:
        geo_stats_data = json.load(geo_stats_file)

        for geo_stat in geo_stats_data:
            geography_id = db.execute(
                text(
                    "select id from geography where value = :iso and type = 'ISO-3166'"
                ),
                params={"iso": geo_stat["iso"]},
            ).scalar()

            if geography_id is None:
                continue

            args = {**geo_stat}
            args["geography_id"] = geography_id
            del args["iso"]

            db.execute(
                text(
                    "insert into geo_statistics ("
                    "name, legislative_process, federal, federal_details, "
                    "political_groups, global_emissions_percent, "
                    "climate_risk_index, worldbank_income_group, visibility_status, "
                    "geography_id "
                    ") values "
                    "("
                    ":name, :legislative_process, :federal, :federal_details, "
                    ":political_groups, :global_emissions_percent, "
                    ":climate_risk_index, :worldbank_income_group, :visibility_status, "
                    ":geography_id"
                    ")"
                ),
                params=args,
            )
    db.flush()


def add_country_subdivisions_from_pycountry(session: Session, geography):
    country_subdivisions = []
    for subdivision in pycountry.subdivisions:
        subdivision = cast(Subdivision, subdivision)
        # if it exists, skip
        existing_subdivision = (
            session.query(geography).filter(geography.value == subdivision.code).first()
        )
        if existing_subdivision is not None:
            print(f"Subdivision already exists: {subdivision.name}, {subdivision.code}")
            continue
        # if it does not have a parent, skip
        # trunk-ignore(pyright/reportGeneralTypeIssues)
        parent_country_alpha_3 = subdivision.country.alpha_3
        parent = (
            session.query(geography)
            .filter(geography.value == parent_country_alpha_3)
            .first()
        )
        if parent is None:
            # No parent found for {subdivision.name}, {subdivision.code}, {parent_country_alpha_3}
            continue

        country_subdivisions.append(
            geography(
                display_value=subdivision.name,
                slug=subdivision.code.lower(),
                value=subdivision.code,
                type="ISO-3166-2",
                parent_id=parent.id if parent else None,
            )
        )

    session.add_all(country_subdivisions)
    session.commit()


def _populate_initial_geographies(session: Session, geography):
    if session.execute(text("select count(*) from geography")).scalar() != 0:
        return

    def _insert_geo_tree(nodes, parent_id=None):
        for entry in nodes:
            data = entry["node"]
            display_value = data["display_value"]
            slug = slugify(display_value, separator="-")
            value = data["value"]
            geo_type = data["type"]
            inserted_id = session.execute(
                text(
                    "insert into geography (display_value, slug, value, type, parent_id) "
                    "values (:display_value, :slug, :value, :type, :parent_id) "
                    "returning id"
                ),
                params={
                    "display_value": display_value,
                    "slug": slug,
                    "value": value,
                    "type": geo_type,
                    "parent_id": parent_id,
                },
            ).scalar_one()

            children = entry.get("children") or []
            if children:
                _insert_geo_tree(children, parent_id=inserted_id)

    geo_data_path = (
        f"{get_library_path()}/data_migrations/data/source/geography_data.json"
    )
    with open(geo_data_path) as geo_data_file:
        geo_data = json.load(geo_data_file)
        _insert_geo_tree(geo_data, parent_id=None)

    add_country_subdivisions_from_pycountry(session, geography)

    for country in pycountry.countries:
        country = cast(Country, country)
        existing_country = (
            session.query(geography).filter(geography.value == country.alpha_3).first()
        )

        # if exists - update with new values
        if existing_country is not None:
            # check if the name and display value match
            name = getattr(country, "common_name", country.name)
            if existing_country.display_value != name:
                session.query(geography).filter(
                    geography.value == country.alpha_3
                ).update({"display_value": name})

            continue

    # Add the Other region (if not already present)
    other_row = session.execute(
        text("select id from geography where value = :val"), params={"val": GEO_OTHER}
    ).scalar_one_or_none()

    if other_row is None:
        other_id = session.execute(
            text(
                "insert into geography (display_value, slug, value, type) "
                "values (:display_value, :slug, :value, :type) returning id"
            ),
            params={
                "display_value": GEO_OTHER,
                "slug": slugify(GEO_OTHER),
                "value": GEO_OTHER,
                "type": "ISO-3166 CPR Extension",
            },
        ).scalar_one()
    else:
        other_id = other_row[0]

    for value, description in CPR_DEFINED_GEOS.items():
        exists = session.execute(
            text("select 1 from geography where value = :value"),
            params={"value": value},
        ).scalar_one_or_none()
        if exists is None:
            session.execute(
                text(
                    "insert into geography (display_value, slug, value, type, parent_id) "
                    "values (:display_value, :slug, :value, :type, :parent_id)"
                ),
                params={
                    "display_value": description,
                    "slug": slugify(value),
                    "value": value,
                    "type": "ISO-3166 CPR Extension",
                    "parent_id": other_id,
                },
            )

    session.flush()


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Populate reference data
    bind = op.get_bind()
    session = Session(bind=bind)

    Base.prepare(autoload_with=bind)
    Org = Base.classes.organisation
    Corpus = Base.classes.corpus
    CorpusType = Base.classes.corpus_type

    # Load CCLW taxonomy from JSON file
    cclw_taxonomy_path = (
        f"{get_library_path()}/data_migrations/data/source/cclw_taxonomy.json"
    )
    with open(cclw_taxonomy_path) as cclw_taxonomy_file:
        cclw_valid_metadata = json.load(cclw_taxonomy_file)

    # Load UNFCCC taxonomy from JSON file
    unfccc_taxonomy_path = (
        f"{get_library_path()}/data_migrations/data/source/unfccc_taxonomy.json"
    )
    with open(unfccc_taxonomy_path) as unfccc_taxonomy_file:
        unfccc_valid_metadata = json.load(unfccc_taxonomy_file)

    # Create Corpus Types
    law_and_policy = add_corpus_type(
        session,
        CorpusType,
        "Laws and Policies",
        "Laws and policies",
        cclw_valid_metadata,
    )
    intl_agreements = add_corpus_type(
        session,
        CorpusType,
        "Intl. agreements",
        "Intl. agreements",
        unfccc_valid_metadata,
    )

    # Create Corpus
    cclw = get_organisation(session, Org, "CCLW")
    if cclw is None:
        cclw = add_organisation(
            session, Org, "CCLW", "LSE CCLW team", "Academic", "CCLW"
        )

    corpus = add_corpus(
        session,
        Corpus,
        "CCLW national policies",
        "CCLW national policies",
        cclw,
        law_and_policy,
        "CCLW national policies",
    )
    session.flush()

    unfccc = get_organisation(session, Org, "UNFCCC")
    if unfccc is None:
        unfccc = add_organisation(
            session,
            Org,
            "UNFCCC",
            "United Nations Framework Convention on Climate Change",
            "UN",
            "UNFCCC",
        )
    corpus = add_corpus(
        session,
        Corpus,
        "UNFCCC Submissions",
        "UNFCCC Submissions",
        unfccc,
        intl_agreements,
        "UNFCCC Submissions",
    )
    session.flush()

    # Geographies
    _populate_initial_geographies(session, Base.classes.geography)

    # Counters
    _populate_counters(session)

    # Geo statistics
    _populate_initial_geo_statistics(session)

    # Languages
    _populate_language(session)

    _populate_document_variants(session, Base.classes.variant)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
