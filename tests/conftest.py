import os
import uuid
from typing import cast

import pytest
from pytest_alembic.config import Config
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import create_engine
from sqlalchemy.engine import (  # pyright: ignore[reportMissingModuleSource]
    URL,
    Engine,
    make_url,
)
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


# Name for our migrated template; no fixture holds a connection to it.
_TEMPLATE_DB_NAME = "db_client_template"


@pytest.fixture(scope="session")
def template_db_engine(template_engine_fixture):
    """
    Create a template database with migrations applied, for use by test_db.

    Uses a dedicated DB name (not the fixture's URL) so no fixture is connected
    to it; we can drop it at session end without ObjectInUse.
    """
    base_url = template_engine_fixture.url
    parsed = cast(URL, make_url(str(base_url)))
    # Use our own DB name; fixture stays connected to its own DB.
    template_url = parsed.set(database=_TEMPLATE_DB_NAME)

    if database_exists(template_url):
        drop_database(template_url)

    create_database(template_url)

    engine = None
    connection = None
    try:
        engine = cast(Engine, create_engine(template_url))
        connection = engine.connect()
        run_migrations(engine)
    finally:
        if connection is not None:
            connection.close()
        if engine is not None:
            engine.dispose()

    yield engine

    if database_exists(template_url):
        drop_database(template_url)


@pytest.fixture(scope="function")
def test_db(template_db_engine):
    """
    Create a fresh test database for each test by cloning the template database.

    Uses a unique DB name per test so only this fixture's engine connects to it;
    teardown can drop the DB without conflicting with pytest-mock-resources.
    """
    template_url = template_db_engine.url
    assert template_url is not None
    parsed = cast(URL, make_url(str(template_url)))
    template_db_name = parsed.database
    db_name = f"test_{uuid.uuid4().hex[:12]}"
    db_url = parsed.set(database=db_name)

    create_database(db_url, template=template_db_name)

    test_session = None
    connection = None
    test_engine = None
    try:
        test_engine = cast(Engine, create_engine(db_url))
        connection = test_engine.connect()

        test_session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
        )
        test_session = test_session_maker()

        yield test_session
    finally:
        if test_session is not None:
            test_session.close()

        if connection is not None:
            connection.close()

        if test_engine is not None:
            test_engine.dispose()

        if database_exists(db_url):
            drop_database(db_url)
