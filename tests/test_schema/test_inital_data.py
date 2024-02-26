from tests.test_schema.helpers import PytestHelpers
from sqlalchemy.orm import Session
from db_client.initial_data import populate_initial_data


def test_initial_data_populates_tables(engine):
    helpers = PytestHelpers(engine)
    helpers.add_alembic()

    with Session(engine) as db:
        populate_initial_data(db, None)
        db.flush()

        geo_count = db.execute("SELECT count(*) FROM geography;").scalar()
        language_count = db.execute("SELECT count(*) FROM language;").scalar()
        geo_stats_count = db.execute("SELECT count(*) FROM geo_statistics;").scalar()

    assert geo_count == 212
    assert language_count == 7893
    assert geo_stats_count == 201