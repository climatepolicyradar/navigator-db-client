from db_client.functions import validate_family_metadata
from db_client.models.dfce.family import Family


def test_validate_metadata_ok(test_engine):

    family = test_engine.query(Family).first()
    validate_family_metadata(test_engine, family)
