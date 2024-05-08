import os
from typing import Generator, cast
import uuid
import pytest
from pytest_alembic.config import Config
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database
from sqlalchemy.engine import Connection, Engine


from db_client import run_migrations
from db_client.functions import add_families
from db_client.functions.dfce_helpers import add_organisation
from db_client.models import Base
from db_client.utils import get_library_path

TEST_FAMILY_1 = {
    "import_id": "CCLW.family.1001.0",
    "corpus_import_id": "CCLW.corpus.i00000001.n0000",
    "title": "Fam1",
    "slug": "FamSlug1",
    "description": "Summary1",
    "geography_id": 1,
    "category": "Executive",
    "documents": [],
    "metadata": {
        "size": "big",
        "color": "pink",
    },
}

TEST_FAMILY_2 = {
    "import_id": "CCLW.family.2002.0",
    "corpus_import_id": "CCLW.corpus.i00000001.n0000",
    "title": "Fam2",
    "slug": "FamSlug2",
    "description": "Summary2",
    "geography_id": 1,
    "category": "Executive",
    "documents": [],
    "metadata": {
        "size": "small",
        "color": "blue",
    },
}


@pytest.fixture
def alembic_config():
    """Override this fixture to configure the exact alembic context setup required."""
    root_dir = get_library_path()
    alembic_ini_path = os.path.join(root_dir, "alembic.ini")
    alembic_scripts_path = os.path.join(root_dir, "alembic")
    return Config(
        config_options={
            "file": alembic_ini_path,
            "script_location": alembic_scripts_path,
            "include_schemas": "db_client",
        }
    )


# Configuration of pytest mock postgres fixtures
@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(image="postgres:14")


# Engine Postgres fixture for alembic tests
alembic_engine = create_postgres_fixture()

# Engine Postgres fixture for our custom tests
test_engine_fixture = create_postgres_fixture()


@pytest.fixture()
def test_engine(test_engine_fixture):
    """Create a test database and use it for the whole test session."""
    if not database_exists(test_engine_fixture.url):
        create_database(test_engine_fixture.url)

    assert len(Base.metadata.sorted_tables) > 1, "sqlalchemy didn't find your model"

    Base.metadata.create_all(test_engine_fixture)

    # Run the tests
    yield test_engine_fixture


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_postgres_fixture()
    yield engine


def get_test_db_url(url: str) -> str:
    return f"{url}_test_{uuid.uuid4()}"


@pytest.fixture(scope="session")
def db_connection(test_db_engine) -> Generator[Connection, None, None]:
    test_db_url = get_test_db_url(test_db_engine.url)

    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)

    saved_db_url = test_engine_fixture.url
    test_engine_fixture.url = test_db_url

    run_migrations(test_db_engine)
    connection = test_engine.connect()

    yield connection
    connection.close()

    test_engine_fixture.url = saved_db_url
    drop_database(test_db_url)


@pytest.fixture(scope="function")
def data_db(db_connection):
    transaction = db_connection.begin()

    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_connection
    )
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()


@pytest.fixture(scope="function")
def db_with_families(data_db):
    org_id = add_organisation(data_db, "TESTORG", "Test Org", "For testing")

    add_families(data_db, families=[TEST_FAMILY_1, TEST_FAMILY_2], org_id=org_id)

    yield data_db
