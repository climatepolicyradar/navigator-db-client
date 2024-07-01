"""
Add more keywords for CCLW metadata

Revision ID: 0028
Revises: 0027
Create Date: 2024-02-26 12:00:00

"""

import json
from string import Template
from typing import Callable, Mapping, Optional, Sequence, Union, cast

import sqlalchemy as sa
from alembic import op
from slugify import slugify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from db_client.data_migrations.taxonomy_utils import read_taxonomy_values
from db_client.models import ORGANISATION_CCLW, ORGANISATION_UNFCCC
from db_client.models.dfce.geography import CPR_DEFINED_GEOS, GEO_OTHER
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
        "filename": f"{get_library_path()}/alembic/versions/0028/cclw/topic_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "sector",
        "filename": f"{get_library_path()}/alembic/versions/0028/cclw/sector_data.json",
        "file_key_path": "node.name",
        "allow_blanks": True,
    },
    {
        "key": "keyword",
        "filename": f"{get_library_path()}/alembic/versions/0028/cclw/keyword_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "instrument",
        "filename": f"{get_library_path()}/alembic/versions/0028/cclw/instrument_data.json",
        "file_key_path": "node.name",
        "allow_blanks": True,
    },
    {
        "key": "hazard",
        "filename": f"{get_library_path()}/alembic/versions/0028/cclw/hazard_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
    {
        "key": "framework",
        "filename": f"{get_library_path()}/alembic/versions/0028/cclw/framework_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
]


def has_rows(db: Session, table: str) -> bool:
    # We can't bind the params to db execute here as parameterising the table name is
    # not an option, so we'll ignore the bandit warning here.
    # trunk-ignore(bandit/B608)
    return cast(int, db.execute(f"select count(*) from {table}").scalar()) > 0


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
    db_international = db.execute(
        "select id from geography where value = 'INT'"
    ).scalar_one_or_none()
    if db_international is not None:
        db_stats = db.execute(
            "select * from geo_statistics where geography_id =  :geo_id",
            params={"geo_id": db_international},
        ).one_or_none()

        if db_stats is not None:
            db.execute(
                "delete from geo_statistics where geography_id =  :geo_id",
                params={"geo_id": db_international},
            )
            db.flush()
        db.execute("delete from geography where value =  'INT'")
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
        f"{get_library_path()}/alembic/versions/0028/geo_stats_updates.json"
    ) as geo_stats_file:
        geo_stats_data = json.load(geo_stats_file)
        for geo_stat in geo_stats_data:
            geography_id = db.execute(
                text(
                    "select id from geography where value = :iso and display_value = :name"
                ),
                params={"iso": geo_stat["iso"], "name": geo_stat["name"]},
            ).scalar()

            geo_stats_id = db.execute(
                text(
                    "select id from geo_statistics where geography_id = :geography_id"
                ),
                params={"geography_id": geography_id},
            ).scalar()

            args = {**geo_stat}
            args["geography_id"] = geography_id
            del args["iso"]

            result = db.execute(
                text(
                    "update geo_statistics set "
                    "name = :name, "
                    "legislative_process = :legislative_process, "
                    "federal = :federal, "
                    "federal_details = :federal_details, "
                    "political_groups = :political_groups, "
                    "global_emissions_percent = :global_emissions_percent, "
                    "climate_risk_index = :climate_risk_index, "
                    "worldbank_income_group = :worldbank_income_group, "
                    "visibility_status = :visibility_status "
                    "where geography_id = :geography_id"
                ),
                params=args,
            )

            if result.rowcount == 0:  # type: ignore
                raise ValueError(
                    f"In geo_stats id: {geo_stats_id} for geo: {geo_stat['name']}"
                )


def _populate_initial_geo_statistics(db: Session) -> None:
    """Populates the geo_statistics table with pre-defined data."""

    if has_rows(db, "geo_statistics"):
        return

    # Load geo_stats data from structured data file
    with open(
        f"{get_library_path()}/alembic/versions/0028/geo_stats_data.json"
    ) as geo_stats_file:
        geo_stats_data = json.load(geo_stats_file)

        for geo_stat in geo_stats_data:
            geography_id = db.execute(
                text(
                    "select id from geography where value = :iso and display_value = :name"
                ),
                params={"iso": geo_stat["iso"], "name": geo_stat["name"]},
            ).scalar()

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


def _populate_counters(db: Session):
    if has_rows(db, "entity_counter"):
        return

    statement = text(
        "insert into entity_counter (prefix, description) values (:prefix, :description)"
    )
    db.execute(
        statement,
        params=[
            {"prefix": ORGANISATION_CCLW, "description": "Counter for CCLW entities"},
            {
                "prefix": ORGANISATION_UNFCCC,
                "description": "Counter for UNFCCC entities",
            },
        ],
    )
    db.commit()


def _populate_language(db: Session) -> None:
    """Populates the language table with pre-defined data."""

    if has_rows(db, "language"):
        return

    with open(
        f"{get_library_path()}/alembic/versions/0028/language_data.json"
    ) as language_file:
        language_data = json.load(language_file)

        query = text(
            "insert into language (language_code, part1_code, part2_code, name) values "
            "(:language_code, :part1_code, :part2_code, :name)"
        )
        db.execute(query, params=language_data)


def _load_family_document_type_data(db: Session, document_type_data: list) -> None:
    query = text(
        "insert into family_document_type (name, description) values "
        "(:name, :description)"
    )
    for _entry in document_type_data:
        found = db.execute(
            "select * from family_document_type where name = :name",
            params={"name": _entry["name"]},
        ).one_or_none()

        if found is not None:
            document_type_data.remove(_entry)
            break

    db.execute(query, params=document_type_data)
    db.flush()


def _populate_document_type(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, "family_document_type"):
        return

    # This is no longer fixed but additive,
    # meaning we will add anything here that is not present in the table
    with open(
        f"{get_library_path()}/alembic/versions/0028/document_type_data.json"
    ) as submission_type_file:
        document_type_data = json.load(submission_type_file)
        _load_family_document_type_data(db, document_type_data)

    with open(
        f"{get_library_path()}/alembic/versions/unfccc/submission_type_data.json"
    ) as submission_type_file:
        submission_type_data = json.load(submission_type_file)
        document_type_data = [
            {"name": e["name"], "description": e["name"]} for e in submission_type_data
        ]
        _load_family_document_type_data(db, document_type_data)


def _populate_document_role(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, "family_document_role"):
        return

    with open(
        f"{get_library_path()}/alembic/versions/0028/document_role_data.json"
    ) as document_role_file:
        document_role_data = json.load(document_role_file)

        query = text(
            "insert into family_document_role ( name, description) values "
            "(:name, :description)"
        )
        db.execute(query, params=document_role_data)


def _populate_document_variant(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, "variant"):
        return

    with open(
        f"{get_library_path()}/alembic/versions/0028/document_variant_data.json"
    ) as document_variant_file:
        document_variant_data = json.load(document_variant_file)

        query = text(
            "insert into variant (variant_name, description) values "
            "(:variant_name, :description)"
        )
        db.execute(query, params=document_variant_data)


def _populate_event_type(db: Session) -> None:
    """Populates the family_event_type table with pre-defined data."""

    if has_rows(db, "family_event_type"):
        return

    with open(
        f"{get_library_path()}/alembic/versions/0028/event_type_data.json"
    ) as event_type_file:
        event_type_data = json.load(event_type_file)

        query = text(
            "insert into family_event_type (name, description) values "
            "(:name, :description)"
        )
        db.execute(query, params=event_type_data)


def _load_tree(
    db: Session,
    data_tree_list: Sequence[Mapping[str, Mapping]],
    parent_id: Optional[int] = None,
    start_id: int = 1,
) -> None:
    current_id = start_id
    for entry in data_tree_list:
        geo_id = current_id
        data = entry["node"]

        db.execute(
            text(
                "insert into geography (display_value, slug, value, type, parent_id) values "
                "(:display_value, :slug, :value, :type, :parent_id)"
            ),
            params={
                "display_value": data["display_value"],
                "slug": data["slug"],
                "value": data["value"],
                "type": data["type"],
                "parent_id": parent_id,
            },
        )

        child_nodes = cast(Sequence[Mapping[str, Mapping]], entry["children"])
        if child_nodes:
            db.flush()
            # Increment the start_id for the next sibling node in the current level
            current_id += len(child_nodes) + 1
            _load_tree(db, child_nodes, geo_id, start_id=geo_id + 1)
        else:
            current_id += 1


def load_tree(
    db: Session,
    data_tree_list: Sequence[Mapping[str, Mapping]],
) -> None:
    """
    Load a tree of data stored as JSON into a database table

    :param [Session] db: An open database session
    :param [AnyModel] table: The table (and therefore type) of entries to create
    :param [Sequence[Mapping[str, Mapping]]] data_tree_list: A tree-list of data to load
    """
    _load_tree(db=db, data_tree_list=data_tree_list, parent_id=None)


def _populate_geography(db: Session) -> None:
    """Populates the geography table with pre-defined data."""

    geo_populated = has_rows(db, "geography")
    if geo_populated:
        return

    # First ensure our defined entries are present
    remove_old_international_geo(db)

    with open(
        f"{get_library_path()}/alembic/versions/0028/geography_data.json"
    ) as geo_data_file:
        geo_data = json.loads(geo_data_file.read())
        _add_geo_slugs(geo_data)
        load_tree(db, geo_data)

    db.flush()

    # Add the Other region
    other = db.execute(
        text("select * from geography where value = :other_geo"),
        params={"other_geo": GEO_OTHER},
    ).one_or_none()
    if other is None:
        other_geo_id = db.execute(
            text("select id from geography order by id desc limit 1"),
        ).one()

        other_geo_id = cast(int, other_geo_id[0])
        other_geo_id += 1

        db.execute(
            text(
                "insert into geography (id, display_value, slug, value, type) values "
                "(:other_geo_id, :other_geo, :other_geo_slug, :other_geo, :other_type)"
            ),
            params={
                "other_geo_id": other_geo_id,
                "other_geo": GEO_OTHER,
                "other_geo_slug": slugify(GEO_OTHER),
                "other_type": "ISO-3166 CPR Extension",
            },
        )
        db.flush()

    else:
        other_geo_id = other[0]

    # Add the CPR geo definitions in Other
    for index, cpr_defined_geo in enumerate(CPR_DEFINED_GEOS.items()):
        value, description = cpr_defined_geo
        db_geo = db.execute(
            text("select * from geography where value = :value"),
            params={"value": value},
        ).one_or_none()
        if db_geo is None:
            db.execute(
                text(
                    "insert into geography ("
                    "id, display_value, slug, value, type, parent_id"
                    ") values "
                    "(:id, :display_value, :slug, :value, :type, :parent_id)"
                ),
                params={
                    "id": other_geo_id + index + 1,
                    "display_value": description,
                    "slug": slugify(value),
                    "value": value,
                    "type": "ISO-3166 CPR Extension",
                    "parent_id": other_geo_id,
                },
            )


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
    if has_rows(session, "organisation"):
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


def get_cclw_id_and_keywords(db: Session):
    Org = Base.classes.organisation
    # Get CCLW as an org
    cclw = db.query(Org).filter(Org.name == "CCLW").one()
    valid_metadata = cclw.metadata_taxonomy_collection[0].valid_metadata
    id = cclw.metadata_taxonomy_collection[0].id

    # Get the keywords
    return id, valid_metadata["keyword"]["allowed_values"]


def do_old_init_data(db: Session):
    # These functions were originally called in the `initial_data.py` script
    # which is now retired in favour of migrations like this
    _populate_document_type(db)
    _populate_document_role(db)
    _populate_document_variant(db)
    _populate_event_type(db)
    _populate_geography(db)
    _populate_language(db)
    _populate_taxonomy(db)
    _populate_counters(db)

    db.flush()  # Geography data is used by geo-stats so flush

    _populate_geo_statistics(db)


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
