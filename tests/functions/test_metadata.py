import pytest
from pydantic import ValidationError
from pytest_mock_resources import create_postgres_fixture

from db_client.functions.metadata import validate_metadata_against_taxonomy
from db_client.models.base import Base
from tests.functions.helpers import family_build, metadata_build

db = create_postgres_fixture(Base, session=True)


EXPECTED_BAD_TAXONOMY = "Bad Taxonomy data in database"


def setup_test(db, taxonomy, metadata):
    org, corpus, _ = metadata_build(db, taxonomy)
    family_build(db, org, corpus, metadata)


def test_validation_fails_when_taxonomy_bad(db):
    taxonomy = {"one": "two", "three": "four"}
    metadata = {"metadata": "anything"}
    setup_test(db, taxonomy, metadata)

    with pytest.raises(TypeError) as e:
        validate_metadata_against_taxonomy(taxonomy, metadata)

    assert str(e.value) == EXPECTED_BAD_TAXONOMY
    inner = e.value.__cause__
    assert inner is not None
    assert inner.args[0] == "Taxonomy entry for 'one' is not a dictionary"


def test_validation_fails_when_taxonomy_missing_allow_blanks(db):
    taxonomy = {
        "author_type": {
            "allowed_values": ["Party", "Non-Party"],
        }
    }
    metadata = {"metadata": "anything"}
    setup_test(db, taxonomy, metadata)
    with pytest.raises(ValidationError) as e:
        validate_metadata_against_taxonomy(taxonomy, metadata)

    assert len(e.value.errors()) == 1
    error = e.value.errors()[0]
    assert error["msg"] == "Field required"
    assert error["type"] == "missing"
    assert error["loc"] == ("allow_blanks",)


def test_validation_fails_when_taxonomy_missing_allowed_values(db):
    taxonomy = {
        "author_type": {
            "allow_blanks": False,
        }
    }
    metadata = {"metadata": "anything"}
    setup_test(db, taxonomy, metadata)
    with pytest.raises(ValidationError) as e:
        validate_metadata_against_taxonomy(taxonomy, metadata)

    assert len(e.value.errors()) == 1
    error = e.value.errors()[0]
    assert error["msg"] == "Field required"
    assert error["type"] == "missing"
    assert error["loc"] == ("allowed_values",)


def test_validation_fails_when_taxonomy_has_extra(db):
    taxonomy = {
        "author_type": {
            "allow_blanks": False,
            "allowed_values": ["Party", "Non-Party"],
            "extra": "field",
        }
    }
    metadata = {"metadata": "anything"}
    setup_test(db, taxonomy, metadata)
    with pytest.raises(ValidationError) as e:
        validate_metadata_against_taxonomy(taxonomy, metadata)

    assert len(e.value.errors()) == 1
    error = e.value.errors()[0]
    assert error["msg"] == "Unexpected keyword argument"
    assert error["type"] == "unexpected_keyword_argument"
    assert error["loc"] == ("extra",)


def test_validation_when_good(db):
    taxonomy = {
        "author_type": {
            "allow_blanks": False,
            "allowed_values": ["Party", "Non-Party"],
        },
        "animals": {
            "allow_blanks": True,
            "allowed_values": [],
            "allow_any": True,
        },
    }
    metadata = {"author_type": ["Party"], "animals": ["sheep"]}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is None


def test_validation_errors_on_extra_keys(db):
    taxonomy = {
        "author_type": {
            "allow_blanks": False,
            "allowed_values": ["Party", "Non-Party"],
        }
    }
    metadata = {"author_type": ["Party"], "animals": ["sheep"]}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Extra metadata keys: {'animals'}"


def test_validation_errors_on_missing_keys(db):
    taxonomy = {
        "author_type": {
            "allow_blanks": False,
            "allowed_values": ["Party", "Non-Party"],
        },
        "animals": {
            "allow_blanks": True,
            "allowed_values": [],
            "allow_any": True,
        },
    }
    metadata = {"author_type": ["Party"]}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Missing metadata keys: {'animals'}"


def test_validation_errors_on_blanks(db):
    taxonomy = {
        "animals": {
            "allow_blanks": False,
            "allowed_values": [],
        },
    }
    metadata = {"animals": []}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Blank value for metadata key 'animals'"


def test_validation_allows_blanks(db):
    taxonomy = {
        "animals": {
            "allow_blanks": True,
            "allowed_values": [],
        },
    }
    metadata = {"animals": []}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is None


def test_validation_errors_on_disallowed_values(db):
    taxonomy = {
        "animals": {
            "allow_blanks": False,
            "allowed_values": ["sheep", "goat"],
        },
    }
    metadata = {"animals": ["cat"]}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == "Invalid value '['cat']' for metadata key 'animals'"


def test_validation_allows_values(db):
    taxonomy = {
        "animals": {
            "allow_blanks": False,
            "allowed_values": ["sheep", "goat"],
        },
    }
    metadata = {"animals": ["sheep"]}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is None


def test_validation_allows_any(db):
    taxonomy = {
        "animals": {
            "allow_blanks": False,
            "allowed_values": ["sheep", "goat"],
            "allow_any": True,
        },
    }
    metadata = {"animals": ["cat"]}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is None


def test_validation_errors_on_non_string_values(db):
    taxonomy = {
        "author_type": {
            "allow_blanks": False,
            "allowed_values": ["Party", "Non-Party"],
        }
    }
    metadata = {"author_type": ["Party", 123, None]}
    setup_test(db, taxonomy, metadata)

    errors = validate_metadata_against_taxonomy(taxonomy, metadata)

    assert errors is not None
    assert len(errors) == 1
    assert errors[0] == (
        "Invalid value(s) in '['Party', 123, None]' for metadata key "
        "'author_type', expected all items to be strings."
    )
