import os
from typing import cast

import pytest
from pytest_alembic.config import Config
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from db_client import run_migrations
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

template_engine_fixture = create_postgres_fixture(scope="session")


@pytest.fixture(scope="session")
def template_db_engine(template_engine_fixture):
    """Create a template database with migrations applied to be used by test_db."""
    db_url = template_engine_fixture.url

    # Drop template if it exists
    if database_exists(db_url):
        drop_database(db_url)

    # Create fresh template database
    create_database(db_url)

    # Apply migrations to template
    engine = None
    connection: Connection | None = None
    try:
        e = cast(Engine, create_engine(db_url))
        engine = e
        connection = e.connect()
        run_migrations(e)
    finally:
        if connection is not None:
            connection.close()
        if engine is not None:
            engine.dispose()

    yield engine

    # Cleanup
    if database_exists(db_url):
        drop_database(db_url)


@pytest.fixture(scope="function")
def test_db(template_db_engine, test_engine_fixture):
    """Create a fresh test database for each test by cloning the template database."""
    db_url = test_engine_fixture.url

    # Drop existing test database if it exists
    if database_exists(db_url):
        drop_database(db_url)

    # Create new test database using template database
    create_database(db_url, template=template_db_engine.url.database)

    test_session = None
    connection: Connection | None = None
    try:
        test_engine = cast(Engine, create_engine(db_url))
        connection = test_engine.connect()

        test_session_maker = sessionmaker(
            bind=test_engine,
            autoflush=False,
        )
        test_session = test_session_maker()

        yield test_session
    finally:
        if test_session is not None:
            test_session.close()

        if connection is not None:
            connection.close()

        # Drop the test database
        drop_database(db_url)
