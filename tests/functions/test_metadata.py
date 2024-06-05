import pytest
from pydantic import ValidationError
from pytest_mock_resources import create_postgres_fixture

from db_client.functions.metadata import validate_family_metadata
from db_client.models.base import Base
from tests.functions.helpers import family_build, metadata_build

db = create_postgres_fixture(Base, session=True)

"""
Test Plan

- Taxonomy not a list
- Bad Taxonomy
- Incomplete Taxonomy
- Extra fields in Taxonomy

- Blank Taxonomy allows any metadata

- Good Taxonomy - bad metadata
- Good Taxonomy - incomplete metadata
- Good Taxonomy - extra metadata
- Good Taxonomy - 

    allow_blanks: bool
    allowed_values: Sequence[str]
    allow_any: bool = False

"""


def setup_test(db, taxonomy, metadata):
    org, corpus, corpus_type = metadata_build(db, taxonomy)
    family = family_build(db, org, corpus, metadata)
    return org, family


def test_validation_fails_when_taxonomy_is_not_a_list(db):
    _, family = setup_test(db, {"taxonomy": "not a list"}, {"metadata": "anything"})
    with pytest.raises(TypeError) as e:
        validate_family_metadata(db, family)
    assert e.value.args[0] == "Taxonomy is not a list"


def test_validation_fails_when_taxonomy_bad(db):
    _, family = setup_test(
        db, [{"one": "two"}, {"three": "four"}], {"metadata": "anything"}
    )

    with pytest.raises(ValidationError) as e:
        validate_family_metadata(db, family)

    assert len(e.value.errors()) == 3


def test_validation_fails_when_taxonomy_missing_allow_blanks(db):
    _, family = setup_test(
        db,
        [
            {
                "author_type": {
                    "allowed_values": ["Party", "Non-Party"],
                }
            }
        ],
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
        [
            {
                "author_type": {
                    "allow_blanks": False,
                }
            }
        ],
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
        [
            {
                "author_type": {
                    "allow_blanks": False,
                    "allowed_values": ["Party", "Non-Party"],
                    "extra": "field",
                }
            }
        ],
        {"metadata": "anything"},
    )
    with pytest.raises(ValidationError) as e:
        validate_family_metadata(db, family)

    assert len(e.value.errors()) == 1
    error = e.value.errors()[0]
    assert error["msg"] == "Unexpected keyword argument"
    assert error["type"] == "unexpected_keyword_argument"
    assert error["loc"] == ("extra",)
