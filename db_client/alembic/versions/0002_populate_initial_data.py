"""Populate initial data

Revision ID: 0002
Revises: 0001
Create Date: 2025-10-30 17:01:09.258758

"""

import json
from typing import cast

import pycountry
from alembic import op
from pycountry.db import Country, Subdivision
from slugify import slugify
from sqlalchemy import func, select
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
    org = session.execute(select(Org).where(Org.name == name)).scalars().one_or_none()
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


def add_corpus(
    session,
    Corpus,
    title,
    description,
    org,
    corpus_type,
    corpus_text,
    corpus_image_url=None,
):
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
        corpus_image_url=corpus_image_url,
        attribution_url=None,
    )
    session.add(corpus)
    session.flush()
    return corpus


def _populate_language(session: Session, language_model) -> None:
    """Populates the language table with pre-defined data."""
    if session.scalar(select(func.count()).select_from(language_model)) == 0:
        language_data_path = (
            f"{get_library_path()}/data_migrations/data/source/language_data.json"
        )
        with open(language_data_path) as language_file:
            language_data = json.load(language_file)
            for language in language_data:
                session.add(
                    language_model(
                        language_code=language["language_code"],
                        part1_code=language.get("part1_code", None),
                        part2_code=language.get("part2_code", None),
                        name=language.get("name", None),
                    )
                )
    session.flush()


def _populate_document_variants(session: Session, variant):
    if session.scalar(select(func.count()).select_from(variant)) == 0:
        session.add(
            variant(variant_name="Original Language", description="Original Language")
        )
        session.add(variant(variant_name="Translation", description="Translation"))
    session.flush()


def _populate_counters(session: Session, entity_counter_model):
    if session.scalar(select(func.count()).select_from(entity_counter_model)) == 0:
        session.add(
            entity_counter_model(prefix="CCLW", description="Counter for CCLW entities")
        )
        session.add(
            entity_counter_model(
                prefix="UNFCCC", description="Counter for UNFCCC entities"
            )
        )
    session.flush()


def _populate_initial_geo_statistics(db: Session, geo_statistics_model) -> None:
    """Populates the geo_statistics table with pre-defined data."""

    if db.scalar(select(func.count()).select_from(geo_statistics_model)) != 0:
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

            db.add(
                geo_statistics_model(
                    name=geo_stat["name"],
                    legislative_process=geo_stat["legislative_process"],
                    federal=geo_stat["federal"],
                    federal_details=geo_stat["federal_details"],
                    political_groups=geo_stat["political_groups"],
                    global_emissions_percent=geo_stat["global_emissions_percent"],
                    climate_risk_index=geo_stat["climate_risk_index"],
                    worldbank_income_group=geo_stat["worldbank_income_group"],
                    visibility_status=geo_stat["visibility_status"],
                    geography_id=geography_id,
                )
            )

    db.flush()


def add_country_subdivisions_from_pycountry(session: Session, geography):
    country_subdivisions = []
    for subdivision in pycountry.subdivisions:
        subdivision = cast(Subdivision, subdivision)
        # if it exists, skip
        existing_subdivision = (
            session.execute(
                select(geography).where(geography.value == subdivision.code)
            )
            .scalars()
            .first()
        )
        if existing_subdivision is not None:
            print(f"Subdivision already exists: {subdivision.name}, {subdivision.code}")
            continue
        # if it does not have a parent, skip
        parent_country_alpha_3 = cast(Country, subdivision.country).alpha_3
        parent = (
            session.execute(
                select(geography).where(geography.value == parent_country_alpha_3)
            )
            .scalars()
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


def _insert_geo_tree(nodes, geography, session: Session, parent_id=None):
    for entry in nodes:
        data = entry["node"]
        display_value = data["display_value"]
        slug = slugify(display_value, separator="-")
        value = data["value"]
        geo_type = data["type"]

        geo_obj = geography(
            display_value=display_value,
            slug=slug,
            value=value,
            type=geo_type,
            parent_id=parent_id,
        )
        session.add(geo_obj)
        session.flush()
        inserted_id = geo_obj.id

        children = entry.get("children") or []
        if children:
            _insert_geo_tree(children, geography, session, parent_id=inserted_id)


def _populate_initial_geographies(session: Session, geography):
    if session.scalar(select(func.count()).select_from(geography)) != 0:
        return

    geo_data_path = (
        f"{get_library_path()}/data_migrations/data/source/geography_data.json"
    )
    with open(geo_data_path) as geo_data_file:
        geo_data = json.load(geo_data_file)
        _insert_geo_tree(geo_data, geography, session, parent_id=None)

    add_country_subdivisions_from_pycountry(session, geography)

    for country in pycountry.countries:
        country = cast(Country, country)
        existing_country = (
            session.execute(select(geography).where(geography.value == country.alpha_3))
            .scalars()
            .first()
        )

        # if exists - update with new values
        if existing_country is not None:
            # check if the name and display value match
            name = getattr(country, "common_name", country.name)
            if existing_country.display_value != name:
                session.execute(
                    text(
                        "update geography set display_value = :name where value = :val"
                    ),
                    {"name": name, "val": country.alpha_3},
                )

            continue

    # Add the Other region (if not already present)
    other_row = session.execute(
        text("select id from geography where value = :val"), params={"val": GEO_OTHER}
    ).scalar_one_or_none()

    if other_row is None:
        other_geo = geography(
            display_value=GEO_OTHER,
            slug=slugify(GEO_OTHER),
            value=GEO_OTHER,
            type="ISO-3166 CPR Extension",
        )
        session.add(other_geo)
        session.flush()
        other_id = other_geo.id
    else:
        other_id = other_row

    for value, description in CPR_DEFINED_GEOS.items():
        exists = session.execute(
            text("select 1 from geography where value = :value"),
            params={"value": value},
        ).scalar_one_or_none()
        if exists is None:
            session.add(
                geography(
                    display_value=description,
                    slug=slugify(value),
                    value=value,
                    type="ISO-3166 CPR Extension",
                    parent_id=other_id,
                )
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

    add_corpus(
        session,
        Corpus,
        "CCLW national policies",
        "CCLW national policies",
        cclw,
        law_and_policy,
        (
            "\n        <p>\n          The summary of this document was written by "
            'researchers at the <a href="http://lse.ac.uk/grantham" target="_blank"> '
            "Grantham Research Institute </a> . \n          If you want to use this summary"
            ', please check <a href="'
            'https://www.lse.ac.uk/granthaminstitute/cclw-terms-and-conditions" target='
            '"_blank"> terms of use </a> for citation and licensing of third party data.'
            "\n        </p>\n"
        ),
        "corpora/CCLW.corpus.i00000001.n0000/logo.png",
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

    add_corpus(
        session,
        Corpus,
        "UNFCCC Submissions",
        "UNFCCC Submissions",
        unfccc,
        intl_agreements,
        (
            "\n        <p>\n          This document was downloaded from "
            'the <a href="https://unfccc.int/" target="_blank"> UNFCCC website </a> . '
            '\n          Please check <a href="https://unfccc.int/this-site/terms-of-use'
            '" target="_blank"> terms of use </a> for citation and licensing of third '
            "party data.\n        </p>\n"
        ),
        None,
    )
    session.flush()

    # Geographies
    _populate_initial_geographies(session, Base.classes.geography)

    # Counters
    _populate_counters(session, Base.classes.entity_counter)

    # Geo statistics
    _populate_initial_geo_statistics(session, Base.classes.geo_statistics)

    # Languages
    _populate_language(session, Base.classes.language)

    _populate_document_variants(session, Base.classes.variant)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
