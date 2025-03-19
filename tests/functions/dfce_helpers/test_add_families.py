from typing import cast

from sqlalchemy.orm import Session

from db_client.functions.dfce_helpers import (
    add_collections,
    add_families,
    link_collection_family,
)
from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import (
    Concept,
    ConceptType,
    Family,
    FamilyCategory,
    FamilyGeography,
)
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
        "metadata": {},
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


def test_add_families__different_categories(test_db):
    """
    This test ensures that a db migration script is added to update the FamilyCategory enum in Postgres
    if the FamilyCategory model was updated.
    """
    basic_family_data = {
        "corpus_import_id": "CCLW.corpus.i00000001.n0000",
        "title": "Title",
        "description": "Summary",
        "geography_id": [2],
        "documents": [],
        "metadata": {
            "size": "small",
            "color": "blue",
        },
    }

    families = []
    for i, category in enumerate(FamilyCategory):
        family = {
            "import_id": f"CCLW.family.3003.{i}",
            "category": category.value,
            "slug": f"FamSlug{i}",
            **basic_family_data,
        }
        families.append(family)

    add_families(test_db, families=families)

    saved_families = test_db.query(Family).all()
    assert len(saved_families) == len(FamilyCategory)


def test_parent_concepts_are_not_included(test_db_no_migrations: Session) -> None:
    test_db = test_db_no_migrations
    """
    These tests are mostly to illustrate how the data works
    and outlines some limitations to the current implementation
    """

    australia = Concept(
        id="AUS",
        type=ConceptType.Country,
        preferred_label="Australia",
    )

    australia_new_south_wales = Concept(
        id="AU-NSW",
        type=ConceptType.CountrySubdivision,
        preferred_label="New South Wales",
        subconcept_of_ids=[australia.id],
    )

    family1 = Family(
        import_id="family1",
        title="Family1",
        description="FamilySummary1",
        family_category=FamilyCategory.EXECUTIVE,
        geographies=[],
        concepts=[australia, australia_new_south_wales],
    )

    test_db.add(family1)
    test_db.commit()

    family_result: Family = test_db.query(Family).get(family1.import_id)

    assert family_result is not None
    assert family_result.parsed_concepts() == [australia, australia_new_south_wales]
