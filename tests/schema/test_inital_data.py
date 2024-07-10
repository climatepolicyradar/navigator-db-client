import logging

import pytest
from sqlalchemy.orm import Session

from db_client.models.organisation.corpus import Corpus, CorpusType, Organisation

EXPECTED_CCLW_TAXONOMY = {
    "topic",
    "keyword",
    "hazard",
    "framework",
    "sector",
    "instrument",
    "event_type",
    "_document",
}
EXPECTED_CCLW_TOPICS = 4
EXPECTED_CCLW_HAZARDS = 81
EXPECTED_CCLW_SECTORS = 23
EXPECTED_CCLW_KEYWORDS = 219
EXPECTED_CCLW_FRAMEWORKS = 3
EXPECTED_CCLW_INSTRUMENTS = 25

EXPECTED_UNFCCC_TAXONOMY = {"author", "author_type", "event_type", "_document"}
EXPECTED_UNFCCC_AUTHOR_TYPES = 2

EXPECTED_DOCUMENT_TAXONOMY_KEYS = 2

EXPECTED_ORGANISATIONS = 2
EXPECTED_EVENT_TYPES = 17
EXPECTED_DOCUMENT_TYPE = 76
EXPECTED_DOCUMENT_ROLE = 10
EXPECTED_DOCUMENT_VARIANT = 2
EXPECTED_GEOGRAPHIES = 212
EXPECTED_LANGUAGES = 7893
EXPECTED_CORPORA = 2
EXPECTED_CORPUS_TYPES = 2
EXPECTED_GEO_STATISTICS = 201
EXPECTED_ENTITY_COUNTER = 2


@pytest.mark.parametrize(
    "table_name, expected_count",
    [
        ("family_document_type", EXPECTED_DOCUMENT_TYPE),
        ("variant", EXPECTED_DOCUMENT_VARIANT),
        ("geography", EXPECTED_GEOGRAPHIES),
        ("language", EXPECTED_LANGUAGES),
        ("organisation", EXPECTED_ORGANISATIONS),
        ("corpus", EXPECTED_CORPORA),
        ("corpus_type", EXPECTED_CORPUS_TYPES),
        ("entity_counter", EXPECTED_ENTITY_COUNTER),
        ("geo_statistics", EXPECTED_GEO_STATISTICS),
    ],
)
def test_initial_data_populated_via_migrations(
    test_db: Session, table_name: str, expected_count: int
):
    count = test_db.execute(f"SELECT count(*) FROM {table_name};").scalar()
    assert count == expected_count


@pytest.mark.parametrize(
    "name, description, organisation_type",
    [
        ("UNFCCC", "United Nations Framework Convention on Climate Change", "UN"),
        ("CCLW", "LSE CCLW team", "Academic"),
    ],
)
def test_organisation_values_correct(
    test_db: Session, name: str, description: str, organisation_type: str
):
    org = test_db.query(Organisation).filter(Organisation.name == name).one_or_none()
    assert org is not None

    assert org.name == name
    assert org.description == description
    assert org.organisation_type == organisation_type


@pytest.mark.parametrize(
    "org_name, corpus_type_name, description, title",
    [
        (
            "UNFCCC",
            "Intl. agreements",
            "UNFCCC Submissions",
            "UNFCCC Submissions",
        ),
        (
            "CCLW",
            "Laws and Policies",
            "CCLW national policies",
            "CCLW national policies",
        ),
    ],
)
def test_corpora_values_correct(
    test_db: Session,
    org_name: str,
    corpus_type_name: str,
    description: str,
    title: str,
):
    corpus = (
        test_db.query(Corpus)
        .join(Organisation, Corpus.organisation_id == Organisation.id)
        .filter(Organisation.name == org_name)
        .one_or_none()
    )

    assert corpus is not None

    assert corpus.import_id is not None
    assert all(parts in corpus.import_id for parts in [org_name, "corpus"])
    assert corpus.corpus_type_name == corpus_type_name
    assert corpus.description == description
    assert corpus.title == title


@pytest.mark.parametrize(
    "org_name, expected_taxonomy_keys, expected_taxonomy_items",
    [
        (
            "UNFCCC",
            EXPECTED_UNFCCC_TAXONOMY,
            [
                ("author_type", EXPECTED_UNFCCC_AUTHOR_TYPES),
                ("event_type", EXPECTED_EVENT_TYPES),
                ("_document", EXPECTED_DOCUMENT_TAXONOMY_KEYS),
            ],
        ),
        (
            "CCLW",
            EXPECTED_CCLW_TAXONOMY,
            [
                ("topic", EXPECTED_CCLW_TOPICS),
                ("hazard", EXPECTED_CCLW_HAZARDS),
                ("sector", EXPECTED_CCLW_SECTORS),
                ("framework", EXPECTED_CCLW_FRAMEWORKS),
                ("keyword", EXPECTED_CCLW_KEYWORDS),
                ("instrument", EXPECTED_CCLW_INSTRUMENTS),
                ("event_type", EXPECTED_EVENT_TYPES),
                ("_document", EXPECTED_DOCUMENT_TAXONOMY_KEYS),
            ],
        ),
    ],
)
def test_taxonomy_value_counts_correct(
    test_db: Session,
    org_name: str,
    expected_taxonomy_keys: set[str],
    expected_taxonomy_items: list[tuple[str, int]],
):
    corpus_type = (
        test_db.query(CorpusType)
        .join(
            Corpus,
            Corpus.corpus_type_name == CorpusType.name,
        )
        .join(Organisation, Organisation.id == Corpus.organisation_id)
        .filter(Organisation.name == org_name)
        .one_or_none()
    )
    assert corpus_type is not None

    schema = corpus_type.valid_metadata
    assert set(schema) ^ expected_taxonomy_keys == set()

    for tax_key, expected_value_count in expected_taxonomy_items:
        if tax_key.startswith("_"):
            assert len(schema[tax_key].keys()) == expected_value_count
        else:
            assert len(schema[tax_key]["allowed_values"]) == expected_value_count


@pytest.mark.parametrize(
    "org_name, expected_taxonomy_items",
    [
        (
            "UNFCCC",
            [
                (
                    "_document",
                    [
                        ("role", EXPECTED_DOCUMENT_ROLE),
                        ("type", EXPECTED_DOCUMENT_TYPE),
                    ],
                ),
            ],
        ),
        (
            "CCLW",
            [
                (
                    "_document",
                    [
                        ("role", EXPECTED_DOCUMENT_ROLE),
                        ("type", EXPECTED_DOCUMENT_TYPE),
                    ],
                ),
            ],
        ),
    ],
)
def test_entity_specific_taxonomy_value_counts_correct(
    test_db: Session,
    org_name: str,
    expected_taxonomy_items: list[tuple[str, list[tuple[str, int]]]],
):
    corpus_type = (
        test_db.query(CorpusType)
        .join(
            Corpus,
            Corpus.corpus_type_name == CorpusType.name,
        )
        .join(Organisation, Organisation.id == Corpus.organisation_id)
        .filter(Organisation.name == org_name)
        .one_or_none()
    )
    assert corpus_type is not None

    # This will make sure that the exact entity keys are present in both the actual and
    # expected entity_keys.
    #
    # This will give us _document, _event, _family etc
    entity_keys = [ek for ek in corpus_type.valid_metadata if ek.startswith("_")]
    expected_entity_keys = [_entity_key for _entity_key, _ in expected_taxonomy_items]

    test_a = set(entity_keys).difference(set(expected_entity_keys))
    if test_a != set():
        logging.error(
            f"Actual entity key(s) {test_a} not present "
            f"in list of expected entity keys {expected_entity_keys}"
        )

    test_b = set(expected_entity_keys).difference(set(entity_keys))
    if test_b != set():
        logging.error(
            f"Expected entity key(s) {test_b} not present "
            f"in list of actual entity keys {entity_keys}"
        )
    assert set(entity_keys) ^ set(expected_entity_keys) == set()

    for entity_specific_key, entity_specific_taxonomy_items in expected_taxonomy_items:
        schema = corpus_type.valid_metadata[entity_specific_key]

        # This will make sure that the exact entity specific keys are present in both the
        # actual and expected entity_specific_keys.
        #
        # This will give us _document taxonomy keys such as role, type etc
        entity_specific_keys = schema.keys()
        expected_entity_specific_keys = [
            _entity_specific_key
            for _, _entity_specific_keys in expected_taxonomy_items
            for _entity_specific_key, __ in _entity_specific_keys
        ]

        test_c = set(entity_specific_keys).difference(
            set(expected_entity_specific_keys)
        )
        if test_c != set():
            logging.error(
                f"Actual entity specific key(s) {test_c} not present "
                f"in list of expected entity specific keys {expected_entity_specific_keys}"
            )

        test_d = set(expected_entity_specific_keys).difference(
            set(entity_specific_keys)
        )
        if test_d != set():
            logging.error(
                f"Expected entity specific key(s) {test_d} not present "
                f"in list of actual entity specific keys {entity_specific_keys}"
            )

        assert set(entity_specific_keys) ^ set(expected_entity_specific_keys) == set()

        for tax_key, expected_value_count in entity_specific_taxonomy_items:
            assert len(schema[tax_key]["allowed_values"]) == expected_value_count
