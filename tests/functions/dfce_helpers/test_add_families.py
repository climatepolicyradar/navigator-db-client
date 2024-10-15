from typing import cast

from db_client.functions.dfce_helpers import (
    add_collections,
    add_families,
    link_collection_family,
)
from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import FamilyGeography
from db_client.models.dfce.geography import Geography


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


def test_add_families__family_geos(test_db):
    document = {
        "title": "Document3",
        "slug": "DocSlug3",
        "md5_sum": None,
        "url": "http://another_somewhere",
        "content_type": None,
        "import_id": "CCLW.executive.3.3",
        "language_variant": None,
        "status": "PUBLISHED",
        "metadata": {"role": ["MAIN"], "type": ["Order"]},
        "languages": [],
        "events": [
            {
                "import_id": "CPR.Event.3.0",
                "title": "Published",
                "date": "2019-12-25",
                "type": "Passed/Approved",
                "status": "OK",
            }
        ],
    }
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
    family["documents"] = [document]
    add_families(test_db, families=[family])

    family_geos = (
        test_db.query(FamilyGeography)
        .filter(FamilyGeography.family_import_id == "CCLW.family.3003.0")
        .all()
    )
    assert len(family_geos) == 2

    ind_id = (
        test_db.query(Geography.id).filter(Geography.display_value == "India").scalar()
    )
    afg_id = (
        test_db.query(Geography.id)
        .filter(Geography.display_value == "Afghanistan")
        .scalar()
    )
    assert all(
        [
            cast(int, family_geo.geography_id) in [ind_id, afg_id]
            for family_geo in family_geos
        ]
    )
