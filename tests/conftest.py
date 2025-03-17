import os

import pytest
from pytest_alembic.config import Config
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from db_client import run_migrations
from db_client.models import Base
from db_client.utils import get_library_path


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


@pytest.fixture(scope="function")
def test_db(test_engine_fixture):
    """Create a fresh test database for each test."""

    test_db_url = test_engine_fixture.url

    # Create the test database
    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)

    test_session = None
    connection = None
    try:
        test_engine = create_engine(test_db_url)
        connection = test_engine.connect()

        run_migrations(test_engine)  # type: ignore for MockConnection

        # Create tables that are not in migrations
        Base.metadata.tables["concept"].create(test_engine)
        Base.metadata.tables["family_concept"].create(test_engine)

        test_session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
        )
        test_session = test_session_maker()

        # Run the tests
        yield test_session
    finally:
        if test_session is not None:
            test_session.close()

        if connection is not None:
            connection.close()  # type: ignore for MockConnection
        # Drop the test database
        drop_database(test_db_url)
