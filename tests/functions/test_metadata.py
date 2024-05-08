from db_client.functions import validate_family_metadata
from db_client.models.dfce.family import Family


def test_this(test_engine):
    assert test_engine != None

def test_validate_metadata_ok(data_db):

    family = data_db.query(Family).first()
    validate_family_metadata(data_db, family)
