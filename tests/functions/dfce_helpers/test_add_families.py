from db_client.functions.dfce_helpers import (
    add_collections,
    add_families,
    link_collection_family,
)
from db_client.models.dfce.collection import CollectionFamily


def test_add_families__link_collection_family(test_db):
    family = {
        "import_id": "CCLW.family.3003.0",
        "corpus_import_id": "CCLW.corpus.i00000001.n0000",
        "title": "Fam3",
        "slug": "FamSlug3",
        "description": "Summary3",
        "geography_id": [2, 5],
        "category": "UNFCCC",
        "documents": [],
        "metadata": {
            "size": "small",
            "color": "blue",
        },
    }
    add_families(test_db, families=[family])

    collection = {
        "import_id": "CPR.Collection.1.0",
        "title": "Collection1",
        "description": "CollectionSummary1",
    }
    add_collections(test_db, collections=[collection])

    link_collection_family(
        test_db, [(str("CPR.Collection.1.0"), str("CCLW.family.3003.0"))]
    )

    collection_family_links = test_db.query(CollectionFamily).all()
    assert len(collection_family_links) == 1

    collection_family_link = collection_family_links[0]  # type: ignore
    assert collection_family_link.collection_import_id == "CPR.Collection.1.0"
    assert collection_family_link.family_import_id == "CCLW.family.3003.0"
