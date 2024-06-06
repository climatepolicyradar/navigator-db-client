import pytest
from pydantic import ValidationError
from pytest_mock_resources import create_postgres_fixture

from db_client.functions.metadata import validate_family_metadata
from db_client.models.base import Base
from tests.functions.helpers import family_build, metadata_build

db = create_postgres_fixture(Base, session=True)


EXPECTED_BAD_TAXONOMY = "Bad Taxonomy data in database"


def setup_test(db, taxonomy, metadata):
    org, corpus, corpus_type = metadata_build(db, taxonomy)
    family = family_build(db, org, corpus, metadata)
    return org, family


def test_validation_fails_when_taxonomy_bad(db):
    _, family = setup_test(
        db, {"one": "two", "three": "four"}, {"metadata": "anything"}
    )

    with pytest.raises(TypeError) as e:
        validate_family_metadata(db, family)

    assert str(e.value) == EXPECTED_BAD_TAXONOMY
    inner = e.value.__cause__
    assert inner is not None
    assert inner.args[0] == "Taxonomy entry for 'one' is not a dictionary"


def test_validation_fails_when_taxonomy_missing_allow_blanks(db):
    _, family = setup_test(
        db,
        {
            "author_type": {
                "allowed_values": ["Party", "Non-Party"],
            }
        },
        {"metadata": "anything"},
    )
    with pytest.raises(ValidationError) as e:
        validate_family_metadata(db, family)

    assert len(e.value.errors()) == 1
    error = e.value.errors()[0]
    assert error["msg"] == "Field required"
    assert error["type"] == "missing"
    assert error["loc"] == ("allow_blanks",)


def test_validation_fails_when_taxonomy_missing_allowed_values(db):
    _, family = setup_test(
        db,
        {
            "author_type": {
                "allow_blanks": False,
            }
        },
        {"metadata": "anything"},
    )
    with pytest.raises(ValidationError) as e:
        validate_family_metadata(db, family)

    assert len(e.value.errors()) == 1
    error = e.value.errors()[0]
    assert error["msg"] == "Field required"
    assert error["type"] == "missing"
    assert error["loc"] == ("allowed_values",)


def test_validation_fails_when_taxonomy_has_extra(db):
    _, family = setup_test(
        db,
        {
            "author_type": {
                "allow_blanks": False,
                "allowed_values": ["Party", "Non-Party"],
                "extra": "field",
            }
        },
        {"metadata": "anything"},
    )
    with pytest.raises(ValidationError) as e:
        validate_family_metadata(db, family)

    assert len(e.value.errors()) == 1
    error = e.value.errors()[0]
    assert error["msg"] == "Unexpected keyword argument"
    assert error["type"] == "unexpected_keyword_argument"
    assert error["loc"] == ("extra",)


def test_validation_when_good(db):
    _, family = setup_test(
        db,
        {
            "author_type": {
                "allow_blanks": False,
                "allowed_values": ["Party", "Non-Party"],
            },
            "animals": {
                "allow_blanks": True,
                "allowed_values": [],
                "allow_any": True,
            },
        },
        {"author_type": ["Party"], "animals": ["sheep"]},
    )

    errors = validate_family_metadata(db, family)

    assert errors is None


def test_validation_errors_on_extra_keys(db):
    _, family = setup_test(
        db,
        {
            "author_type": {
                "allow_blanks": False,
                "allowed_values": ["Party", "Non-Party"],
            }
        },
        {"author_type": ["Party"], "animals": ["sheep"]},
    )

    errors = validate_family_metadata(db, family)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Extra metadata keys: {'animals'}"


def test_validation_errors_on_missing_keys(db):
    _, family = setup_test(
        db,
        {
            "author_type": {
                "allow_blanks": False,
                "allowed_values": ["Party", "Non-Party"],
            },
            "animals": {
                "allow_blanks": True,
                "allowed_values": [],
                "allow_any": True,
            },
        },
        {
            "author_type": ["Party"],
        },
    )

    errors = validate_family_metadata(db, family)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Missing metadata keys: {'animals'}"


def test_validation_errors_on_blanks(db):
    _, family = setup_test(
        db,
        {
            "animals": {
                "allow_blanks": False,
                "allowed_values": [],
            },
        },
        {"animals": []},
    )

    errors = validate_family_metadata(db, family)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Blank value for metadata key 'animals'"


def test_validation_allows_blanks(db):
    _, family = setup_test(
        db,
        {
            "animals": {
                "allow_blanks": True,
                "allowed_values": [],
            },
        },
        {"animals": []},
    )

    errors = validate_family_metadata(db, family)

    assert errors is None


def test_validation_errors_on_disallowed_values(db):
    _, family = setup_test(
        db,
        {
            "animals": {
                "allow_blanks": False,
                "allowed_values": ["sheep", "goat"],
            },
        },
        {"animals": ["cat"]},
    )

    errors = validate_family_metadata(db, family)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Invalid value '['cat']' for metadata key 'animals'"


def test_validation_allows_values(db):
    _, family = setup_test(
        db,
        {
            "animals": {
                "allow_blanks": False,
                "allowed_values": ["sheep", "goat"],
            },
        },
        {"animals": ["sheep"]},
    )

    errors = validate_family_metadata(db, family)

    assert errors is None


def test_validation_allows_any(db):
    _, family = setup_test(
        db,
        {
            "animals": {
                "allow_blanks": False,
                "allowed_values": ["sheep", "goat"],
                "allow_any": True,
            },
        },
        {"animals": ["cat"]},
    )

    errors = validate_family_metadata(db, family)

    assert errors is None
