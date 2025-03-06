from db_client.functions.dfce_helpers import add_collections
from db_client.models.dfce.collection import Collection, CollectionOrganisation


def test_add_collections__one_collection(test_db):
    collection1 = {
        "import_id": "CPR.Collection.1.0",
        "title": "Collection1",
        "description": "CollectionSummary1",
        "valid_metadata": {"key": "value"},
    }
    add_collections(test_db, collections=[collection1])

    collections = test_db.query(Collection).all()
    assert len(collections) == 1

    collection = collections[0]
    assert collection.import_id == "CPR.Collection.1.0"
    assert collection.title == "Collection1"
    assert collection.description == "CollectionSummary1"
    assert collection.valid_metadata == {"key": "value"}


def test_add_collections__multiple_collections(test_db):
    collection1 = {
        "import_id": "CPR.Collection.1.0",
        "title": "Collection1",
        "description": "CollectionSummary1",
        "valid_metadata": {},
    }
    collection2 = {
        "import_id": "CPR.Collection.2.0",
        "title": "Collection2",
        "description": "CollectionSummary2",
        "valid_metadata": {},
    }
    add_collections(test_db, collections=[collection1, collection2])

    collections = test_db.query(Collection).all()
    assert len(test_db.query(Collection).all()) == 2

    assert all(
        [
            collection.import_id in ["CPR.Collection.1.0", "CPR.Collection.2.0"]
            for collection in collections
        ]
    )


def test_add_collections__organisations(test_db):
    collection1 = {
        "import_id": "CPR.Collection.1.0",
        "title": "Collection1",
        "description": "CollectionSummary1",
        "valid_metadata": {},
    }
    add_collections(test_db, collections=[collection1])

    assert len(test_db.query(Collection).all()) == 1

    collections = test_db.query(CollectionOrganisation).all()
    assert len(collections) == 1

    collection = collections[0]
    assert collection.collection_import_id == "CPR.Collection.1.0"
    assert collection.organisation_id == 1
