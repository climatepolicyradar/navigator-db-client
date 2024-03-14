# import contextlib
import logging
import os

import pytest
from pytest_alembic.config import Config
from sqlalchemy_utils import create_database, database_exists

from db_client.models import Base

from pytest_mock_resources import create_postgres_fixture, PostgresConfig

from db_client.utils import get_library_path


_LOGGER = logging.getLogger(__name__)
_LOGGER.info("test")


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
@pytest.fixture(scope='session')
def pmr_postgres_config():
    return PostgresConfig(image='postgres:14')

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
