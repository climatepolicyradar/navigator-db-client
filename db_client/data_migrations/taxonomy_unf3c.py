from db_client.data_migrations.taxonomy_utils import read_taxonomy_values
from db_client.utils import get_library_path

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
    {
        "key": "event_type",
        "filename": f"{get_library_path()}/data_migrations/data/law_policy/event_type_data.json",
        "file_key_path": "name",
        "allow_blanks": True,
    },
]


def get_unf3c_taxonomy():
    return read_taxonomy_values(TAXONOMY_DATA)
