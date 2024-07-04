import pytest

from db_client.functions.metadata import get_entity_specific_taxonomy

EXPECTED_BAD_TAXONOMY = "Bad Taxonomy data in database"


def test_original_taxonomy_is_none():
    assert get_entity_specific_taxonomy(None) is None


def test_original_taxonomy_is_not_none_and_no_entity_key_given():
    taxonomy = {
        "animals": {
            "allow_blanks": True,
            "allowed_values": [],
            "allow_any": True,
        },
    }
    assert get_entity_specific_taxonomy(taxonomy) == taxonomy


def test_original_taxonomy_is_not_none_and_entity_key_given_but_not_valid():
    taxonomy = {
        "animals": {
            "allow_blanks": True,
            "allowed_values": [],
            "allow_any": True,
        },
    }
    with pytest.raises(TypeError) as e:
        get_entity_specific_taxonomy(taxonomy, "fruits")
    assert str(e.value) == "Cannot find fruits taxonomy data in database"


def test_original_taxonomy_is_not_none_and_entity_key_given_and_valid():
    foods_taxonomy = {
        "fruits": {
            "allow_blanks": True,
            "allowed_values": [],
            "allow_any": True,
        },
        "vegetables": {
            "allow_blanks": False,
            "allowed_values": ["leek", "carrot", "potato"],
            "allow_any": False,
        },
    }
    taxonomy = {
        "animals": {
            "allow_blanks": True,
            "allowed_values": [],
            "allow_any": True,
        },
        "foods": foods_taxonomy,
    }
    assert get_entity_specific_taxonomy(taxonomy, "foods") == foods_taxonomy
