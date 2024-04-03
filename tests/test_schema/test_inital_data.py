from typing import Any

from sqlalchemy.orm import Session

from db_client.data_migrations import (
    populate_counters,
    populate_document_role,
    populate_document_type,
    populate_document_variant,
    populate_event_type,
    populate_geo_statistics,
    populate_geography,
    populate_language,
)
from tests.test_schema.helpers import PytestHelpers

POPULATE_FUNCS = [
    (populate_document_type, "family_document_type", 76),
    (populate_document_role, "family_document_role", 10),
    (populate_document_variant, "variant", 2),
    (populate_event_type, "family_event_type", 17),
    (populate_geography, "geography", 212),
    (populate_language, "language", 7893),
    (populate_counters, "entity_counter", 2),
    (populate_geo_statistics, "geo_statistics", 201),
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
