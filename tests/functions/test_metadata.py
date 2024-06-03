from pytest_mock_resources import create_postgres_fixture

from db_client.functions.metadata import validate_family_metadata
from db_client.models.base import Base
from tests.functions.helpers import family_build, metadata_build

db = create_postgres_fixture(Base, session=True)


def test_this(db):
    org, corpus, corpus_type = metadata_build(db, {})
    family = family_build(db, org, corpus, {"this": "that"})

    assert db is not None
    result = validate_family_metadata(db, family)
    assert len(result) == 2
