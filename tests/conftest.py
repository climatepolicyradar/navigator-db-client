import contextlib
import logging
import os

import pytest
from pytest_alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from db_client.models import Base
from tests.test_schema.helpers import clean_tables

test_db_url = str(os.getenv("DATABASE_URL"))

_LOGGER = logging.getLogger(__name__)
_LOGGER.info("test")


@pytest.fixture
def alembic_config():
    """Override this fixture to configure the exact alembic context setup required."""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    alembic_ini_path = os.path.join(root_dir, "db_client", "alembic.ini")
    alembic_scripts_path = os.path.join(root_dir, "db_client", "alembic")
    return Config(
        config_options={
            "file": alembic_ini_path,
            "script_location": alembic_scripts_path,
            "include_schemas": "db_client",
        }
    )


@pytest.fixture()
def alembic_engine():
    """Create a test database and use it for the whole test session."""

    test_engine = create_engine(test_db_url)
    # session_cls = sessionmaker(test_engine)

    # Create the test database
    if database_exists(test_engine.url):
        # Base.metadata.drop_all(test_engine)
        drop_database(test_db_url)

    create_database(test_db_url)

    assert len(Base.metadata.sorted_tables) > 1, "sqlalchemy didn't find your model"
    Base.metadata.create_all(test_engine)

    # Run the tests
    yield test_engine

    # with contextlib.closing(session_cls()) as session:
    #     clean_tables(session, set(), Base)

    # Drop the test database
    Base.metadata.drop_all(test_engine)
    # drop_database(test_db_url)
