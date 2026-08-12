from itertools import groupby
from typing import cast

import pytest
from pydantic import ValidationError
from sqlalchemy import select
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

    collection_family_links = (
        test_db.execute(select(CollectionFamily)).unique().scalars().all()
    )
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
                "valid_metadata": {
                    "datetime_event_name": ["Passed/Approved"],
                },
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
        test_db.execute(
            select(FamilyGeography).where(
                FamilyGeography.family_import_id == "CCLW.family.3003.0"
            )
        )
        .scalars()
        .all()
    )
    assert len(family_geos) == 2

    ind_id = test_db.execute(
        select(Geography.id).where(Geography.display_value == "India")
    ).scalar_one_or_none()
    afg_id = test_db.execute(
        select(Geography.id).where(Geography.display_value == "Afghanistan")
    ).scalar_one_or_none()
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

    saved_families = test_db.execute(select(Family)).unique().scalars().all()
    assert len(saved_families) == len(FamilyCategory)


def test_add_family_with_concepts(test_db: Session):
    concepts = [
        Concept(
            id="Suits against governments",
            type=ConceptType.LegalCategory,
            preferred_label="Suits against governments",
            relation="category",
        ),
        Concept(
            id="Energy and power",
            type=ConceptType.LegalCategory,
            preferred_label="Energy and power",
            relation="category",
            subconcept_of_labels=["Suits against governments"],
        ),
        Concept(
            id="Environmental Crimes",
            type=ConceptType.LegalCategory,
            preferred_label="Environmental Crimes",
            relation="category",
            subconcept_of_labels=["Environmental Crimes"],
        ),
        Concept(
            id="BRA",
            type=ConceptType.Country,
            preferred_label="Brazil",
            relation="jurisdiction",
        ),
        Concept(
            id="BR-RO",
            type=ConceptType.CountrySubdivision,
            preferred_label="Rondônia",
            relation="jurisdiction",
            subconcept_of_labels=["Brazil"],
        ),
        Concept(
            id="Rondônia State Court",
            type=ConceptType.LegalEntity,
            preferred_label="Rondônia State Court",
            relation="jurisdiction",
            subconcept_of_labels=["Rondônia"],
        ),
    ]
    family = Family(
        import_id="family_with_concepts",
        title="Family 3",
        description="Summary 3",
        family_category=FamilyCategory.UNFCCC,
        concepts=concepts,
    )
    test_db.add(family)
    test_db.commit()

    family = (
        test_db.execute(
            select(Family).where(Family.import_id == "family_with_concepts")
        )
        .scalars()
        .first()
    )
    assert family is not None
    assert family.parsed_concepts() == concepts


def test_add_family_with_invalid_concepts(test_db: Session):
    concepts = [
        Concept(
            id="Suits against governments",
            type=ConceptType.LegalCategory,
            preferred_label="Suits against governments",
            relation="category",
        ),
        Concept(
            id="Energy and power",
            type=ConceptType.LegalCategory,
            preferred_label="Energy and power",
            relation="category",
            subconcept_of_labels=["Suits against governments"],
        ),
        Concept(
            id="Environmental Crimes",
            type=ConceptType.LegalCategory,
            preferred_label="Environmental Crimes",
            relation="category",
            subconcept_of_labels=["Environmental Crimes"],
        ),
        Concept(
            id="BRA",
            type=ConceptType.Country,
            preferred_label="Brazil",
            relation="jurisdiction",
        ),
        Concept(
            id="BR-RO",
            type=ConceptType.CountrySubdivision,
            preferred_label="Rondônia",
            relation="jurisdiction",
            subconcept_of_labels=["Brazil"],
        ),
        Concept(
            id="Rondônia State Court",
            type=ConceptType.LegalEntity,
            preferred_label="Rondônia State Court",
            relation="jurisdiction",
            subconcept_of_labels=["Rondônia"],
        ),
    ]

    with pytest.raises(AttributeError):
        concepts_of_invalid_type = {"id": "invalid_concept"}
        family = Family(
            import_id="family_with_concepts",
            title="Family 3",
            description="Summary 3",
            family_category=FamilyCategory.UNFCCC,
            concepts=concepts + [concepts_of_invalid_type],
        )
        test_db.add(family)
        test_db.commit()

    with pytest.raises(ValidationError):
        concept_with_invalid_relation = Concept(
            id="Rondônia State Court",
            type=ConceptType.LegalEntity,
            preferred_label="Rondônia State Court",
            relation="invalid_relation",
            subconcept_of_labels=["Rondônia"],
        )
        family = Family(
            import_id="family_with_concepts",
            title="Family 3",
            description="Summary 3",
            family_category=FamilyCategory.UNFCCC,
            concepts=concepts + [concept_with_invalid_relation],
        )
        test_db.add(family)
        test_db.commit()


def test_family_concepts(test_db: Session):
    """
    These test proves that the first iteration of the model will:
    - support what we need for initial rendering of data
    - be possible to extract this information in this shape in the data-mappers

    It is intentionally sparse e.g. not relying on IDs as this would start to couple us to
    patterns that we might not want going forward.
    """
    # https://climatecasechart.com/non-us-case/santo-antonio-energia-sa-vs-sedam-administrative-fine-for-illegal-burning/
    suits_against_governments = Concept(
        id="Suits against governments",
        type=ConceptType.LegalCategory,
        preferred_label="Suits against governments",
        relation="category",
    )
    energy_and_power = Concept(
        id="Energy and power",
        type=ConceptType.LegalCategory,
        preferred_label="Energy and power",
        relation="category",
        subconcept_of_labels=[suits_against_governments.preferred_label],
    )
    environmental_crimes = Concept(
        id="Environmental Crimes",
        type=ConceptType.LegalCategory,
        preferred_label="Environmental Crimes",
        relation="category",
        subconcept_of_labels=[suits_against_governments.preferred_label],
    )

    brazil_jurisdiction = Concept(
        id="BRA",
        type=ConceptType.Country,
        preferred_label="Brazil",
        relation="jurisdiction",
    )
    rondonia = Concept(
        id="BR-RO",
        type=ConceptType.CountrySubdivision,
        preferred_label="Rondônia",
        relation="jurisdiction",
        subconcept_of_labels=[brazil_jurisdiction.preferred_label],
    )
    rondonia_state_court = Concept(
        id="Rondônia State Court",
        type=ConceptType.LegalEntity,
        preferred_label="Rondônia State Court",
        relation="jurisdiction",
        subconcept_of_labels=[rondonia.preferred_label],
    )

    brazil_law = Concept(
        id="BRA",
        type=ConceptType.Country,
        preferred_label="Brazil",
        relation="principal_law",
    )
    brazil_federal_constitution = Concept(
        id="Brazil Federal Constitution",
        type=ConceptType.Law,
        preferred_label="Brazil Federal Constitution",
        relation="principal_law",
        subconcept_of_labels=[brazil_law.preferred_label],
    )
    art_225 = Concept(
        id="art. 225",
        type=ConceptType.Law,
        preferred_label="art. 225",
        relation="principal_law",
        subconcept_of_labels=[brazil_federal_constitution.id],
    )

    international_law = Concept(
        id="International Law",
        type=ConceptType.Law,
        preferred_label="International Law",
        relation="principal_law",
    )
    unfccc = Concept(
        id="UNFCCC",
        type=ConceptType.Law,
        preferred_label="UNFCCC",
        relation="principal_law",
        subconcept_of_labels=[international_law.preferred_label],
    )
    paris_agreement = Concept(
        id="Paris Agreement",
        type=ConceptType.Law,
        preferred_label="Paris Agreement",
        relation="principal_law",
        subconcept_of_labels=[unfccc.preferred_label],
    )

    paris_agreement_enacted_by_decree_9073_2017 = Concept(
        id="Paris Agreement (enacted by Decree 9073/2017)",
        type=ConceptType.Law,
        preferred_label="Paris Agreement (enacted by Decree 9073/2017)",
        relation="principal_law",
        subconcept_of_labels=[brazil_law.preferred_label],
    )
    national_policy_on_climate_change_pnmc_federal_law_12 = Concept(
        id="National Policy on Climate Change – PNMC (Federal Law 12",
        type=ConceptType.Law,
        preferred_label="National Policy on Climate Change – PNMC (Federal Law 12",
        relation="principal_law",
        subconcept_of_labels=[brazil_law.preferred_label],
    )
    forest_code_law_12_651_2012 = Concept(
        id="Forest Code (Law 12 651/2012)",
        type=ConceptType.Law,
        preferred_label="Forest Code (Law 12 651/2012)",
        relation="principal_law",
        subconcept_of_labels=[brazil_law.preferred_label],
    )
    environmental_crimes_law = Concept(
        id="Environmental Crimes Law",
        type=ConceptType.Law,
        preferred_label="Environmental Crimes Law",
        relation="principal_law",
        subconcept_of_labels=[brazil_law.preferred_label],
    )

    concepts = [
        suits_against_governments,
        energy_and_power,
        environmental_crimes,
        brazil_jurisdiction,
        rondonia,
        rondonia_state_court,
        brazil_law,
        brazil_federal_constitution,
        art_225,
        international_law,
        unfccc,
        paris_agreement,
        paris_agreement_enacted_by_decree_9073_2017,
        national_policy_on_climate_change_pnmc_federal_law_12,
        forest_code_law_12_651_2012,
        environmental_crimes_law,
    ]

    leaves = find_leaf_concepts(concepts)
    paths = generate_concept_paths(leaves, concepts)
    groups = group_concept_paths_by_relation(paths)

    expected_groups = {
        "category": [
            [suits_against_governments, energy_and_power],
            [suits_against_governments, environmental_crimes],
        ],
        "jurisdiction": [
            [brazil_jurisdiction, rondonia, rondonia_state_court],
        ],
        "principal_law": [
            [brazil_law, brazil_federal_constitution, art_225],
            [international_law, unfccc, paris_agreement],
            [brazil_law, paris_agreement_enacted_by_decree_9073_2017],
            [brazil_law, national_policy_on_climate_change_pnmc_federal_law_12],
            [brazil_law, forest_code_law_12_651_2012],
            [brazil_law, environmental_crimes_law],
        ],
    }
    assert groups == expected_groups


def find_leaf_concepts(concepts: list[Concept]) -> list[Concept]:
    # Get all concept IDs that appear as parents in subconcept_of_labels
    parent_labels = {
        parent_label
        for concept in concepts
        for parent_label in concept.subconcept_of_labels
    }
    # Return concepts whose IDs are not in parent_labels (meaning they don't have any children)
    return [
        concept for concept in concepts if concept.preferred_label not in parent_labels
    ]


def generate_concept_paths(
    leaves: list[Concept], concepts: list[Concept]
) -> list[list[Concept]]:
    # Create a mapping of `relation/preferred_label` => concepts for an easy lookup
    concept_label_map = {
        f"{concept.relation}/{concept.preferred_label}": concept for concept in concepts
    }

    def build_path(concept: Concept) -> list[Concept]:
        """Recursively build a path from a concept up to its root."""
        if not concept.subconcept_of_labels:
            return [concept]

        parent_label = concept.subconcept_of_labels[0]
        parent_relation = concept.relation
        parent_concept = concept_label_map.get(f"{parent_relation}/{parent_label}")
        if not parent_concept:
            return [concept]

        return [concept] + build_path(parent_concept)

    paths = [build_path(leaf) for leaf in leaves]
    for path in paths:
        # as this is relatively ring-fenced I don't mind the in-place
        # mutation reverse as it's more readable - although not sure if
        # this comment negates that
        path.reverse()

    return paths


def group_concept_paths_by_relation(
    paths: list[list[Concept]],
) -> dict[str, list[list[Concept]]]:
    # Group paths by the relation of their last concept
    grouped_paths = {
        relation: list(group)
        for relation, group in groupby(paths, key=lambda path: path[-1].relation)
    }

    return grouped_paths
