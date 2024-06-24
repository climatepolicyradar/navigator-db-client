from typing import Optional

from db_client.data_migrations.taxonomy_utils import read_taxonomy_values

TAXONOMY_DATA = [
    {
        "key": "author_type",
        "allow_blanks": False,
        "allowed_values": ["Party", "Non-Party"],
    },
    {
        "key": "author",
        "allow_blanks": False,
        "allow_any": True,
        "allowed_values": [],
    },
]


def get_unf3c_taxonomy(taxonomy_data: Optional[list[dict]] = None):
    if taxonomy_data is None:
        taxonomy_data = TAXONOMY_DATA
    return read_taxonomy_values(taxonomy_data)
