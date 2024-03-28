from typing import Any

from sqlalchemy.orm import Session

from db_client.data_migrations.populate_counters import _populate_counters
from db_client.data_migrations.populate_document_role import _populate_document_role
from db_client.data_migrations.populate_document_type import _populate_document_type
from db_client.data_migrations.populate_document_variant import (
    _populate_document_variant,
)
from db_client.data_migrations.populate_event_type import _populate_event_type
from db_client.data_migrations.populate_geo_statistics import _populate_geo_statistics
from db_client.data_migrations.populate_geography import _populate_geography
from db_client.data_migrations.populate_language import _populate_language
from db_client.data_migrations.populate_taxonomy import _populate_taxonomy
from tests.test_schema.helpers import PytestHelpers

POPULATE_FUNCS = [
    (_populate_document_type, "family_document_type", 76),
    (_populate_document_role, "family_document_role", 10),
    (_populate_document_variant, "variant", 2),
    (_populate_event_type, "family_event_type", 17),
    (_populate_geography, "geography", 212),
    (_populate_language, "language", 7893),
    (_populate_taxonomy, "metadata_taxonomy", 2),
    (_populate_counters, "entity_counter", 2),
    (_populate_geo_statistics, "geo_statistics", 201),
]


def test_initial_data_populates_tables(test_engine: Any):
    helpers = PytestHelpers(test_engine)
    helpers.add_alembic()

    with Session(test_engine) as db:
        for populate_function, table_name, expected_count in POPULATE_FUNCS:
            populate_function(db)
            db.flush()
            count = db.execute(f"SELECT count(*) FROM {table_name};").scalar()

            assert count == expected_count, table_name
