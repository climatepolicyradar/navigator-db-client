import pytest
from sqlalchemy.orm import Session

from db_client.models.dfce.concept import Concept, ConceptType, FamilyConcept
from db_client.models.dfce.family import Family, FamilyCategory


@pytest.mark.asyncio
async def test_parent_concepts_are_not_included(test_db: Session) -> None:
    """
    These tests are mostly to illustrate how the data works
    and outlines some limitations to the current implementation
    """
    family1 = Family(
        import_id="family1",
        title="Family1",
        description="FamilySummary1",
        family_category=FamilyCategory.EXECUTIVE,
        geographies=["GB"],
    )

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

    family_concept_nsw = FamilyConcept(
        family_import_id=family1.import_id,
        concept_id=australia_new_south_wales.id,
        relation="jurisdiction",
    )

    test_db.add(australia)
    test_db.add(australia_new_south_wales)
    test_db.add(family1)
    test_db.commit()
    test_db.add(family_concept_nsw)
    test_db.commit()

    family_result: Family = test_db.query(Family).get(family1.import_id)
    assert family_result is not None
    assert family_result.concepts == [australia_new_south_wales]
