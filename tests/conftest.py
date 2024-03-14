# import contextlib
import logging
import os
import psycopg2

import pytest
from pytest_alembic.config import Config
from sqlalchemy import MetaData, create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from db_client.models import Base

from pytest_mock_resources import create_postgres_fixture, PostgresConfig

# from tests.test_schema.helpers import clean_tables

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

# Configuration of postgres fixture
@pytest.fixture(scope='session')
def pmr_postgres_config():
    return PostgresConfig(image='postgres:14')

# Postgres fixture (using Docker implicily) for alembic tests
alembic_engine = create_postgres_fixture()
test_engine_fixture = create_postgres_fixture()

@pytest.fixture()
def test_engine(test_engine_fixture):
    """Create a test database and use it for the whole test session."""
    metadata = MetaData(bind=test_engine_fixture)
    
    # Asegúrate de que tu URL de conexión es la correcta para el test_engine_fixture
    if not database_exists(test_engine_fixture.url):
        create_database(test_engine_fixture.url)
    
    assert len(Base.metadata.sorted_tables) > 1, "sqlalchemy didn't find your model"
    
    Base.metadata.create_all(test_engine_fixture)

    # Run the tests
    yield test_engine_fixture

    # Eliminar las tablas después de la ejecución de las pruebas
    Base.metadata.drop_all(test_engine_fixture)
