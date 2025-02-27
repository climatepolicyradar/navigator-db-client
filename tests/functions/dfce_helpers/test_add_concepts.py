from db_client.models.dfce.concept import Concept, FamilyConcept
from db_client.models.dfce.family import Family, FamilyCategory


def test_add_concepts(test_db):
    concept1 = Concept(
        id="Q1209",
        preferred_label="organisation and governance instrument",
        alternative_labels=["organisation instrument"],
        negative_labels=[],
        description="Organisation and governance instruments let governments act directly on individuals, property, or the environment, enhancing institutions' capacity for climate action through new roles, bodies, and strategies.",
        wikibase_id="Q1209",
        subconcept_of=["Q1171"],
        has_subconcept=["Q1292", "Q1293", "Q1294", "Q1295", "Q1296"],
        related_concepts=[],
        definition='Allows governments to act directly on individuals, their property, or the environment, focusing on "effecting" rather than detecting. In climate policy, they are designed to enhance institutions\' capacity to address climate change. This includes granting new responsibilities to existing bodies, creating new institutions, and developing governance plans and strategies.',
    )
    family1 = Family(
        import_id="Family1",
        title="Family1",
        description="FamilySummary1",
        family_category=FamilyCategory.EXECUTIVE,
    )

    family_concept1 = FamilyConcept(
        family_import_id=family1.import_id,
        concept_id=concept1.id,
    )
    test_db.add(concept1)
    test_db.add(family1)
    test_db.commit()

    test_db.add(family_concept1)
    test_db.commit()

    concepts = test_db.query(Concept).all()
    assert len(concepts) == 1

    families = test_db.query(Family).all()
    assert len(families) == 1

    print(families[0])
