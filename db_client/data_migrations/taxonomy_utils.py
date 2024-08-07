"""At the moment taxonomy is kept simple, and only supports string validation for enums

For Example:

{
    "topic": {
       allowed_values: [],
       allow_blanks: false,
    },
    ...
}

These functions allow you to reference the values within the json.
See sector_data.json for example each element in the array contains an object where
we use the "node.name" as the taxonomy values:

  {
    "node": {
      "name": "Energy",
      "description": "Energy",
      "source": "CCLW"
    },
    "children": []
  },

This is referenced in the "file_key_path" as the values to be used when a file is
loaded:

    {
        "key": "sector",
        "filename": f"{get_library_path()}/alembic/versions/data/0028/cclw/sector_data.json",
        "file_key_path": "node.name",
        "allow_blanks": True,
    },

"""

import json
from dataclasses import asdict
from typing import Any, Mapping, Sequence

from db_client.models.dfce.taxonomy_entry import TaxonomyEntry


def _dot_dref(obj: dict, dotted_key: str):
    if "." not in dotted_key:
        return obj[dotted_key]
    keys = dotted_key.split(".", 1)
    return _dot_dref(obj[keys[0]], keys[1])


def _load_metadata_type(filename: str, key_path: str) -> Sequence[str]:
    with open(filename) as file:
        data = json.load(file)
    return [_dot_dref(obj, key_path) for obj in data]


def _maybe_read(data: dict[str, Any]) -> TaxonomyEntry:
    if not data["key"].startswith("_"):
        if "filename" in data:
            return TaxonomyEntry(
                allowed_values=_load_metadata_type(
                    data["filename"], data["file_key_path"]
                ),
                allow_blanks=data["allow_blanks"],
                allow_any=False,
            )
        else:
            return TaxonomyEntry(
                allowed_values=data["allowed_values"],
                allow_blanks=data["allow_blanks"],
                allow_any=data.get("allow_any", False),
            )

    return _maybe_read(data["taxonomy"])


def read_taxonomy_values(taxonomy_data: list[dict[str, Any]]) -> Mapping[str, dict]:
    taxonomy = {}
    for data in taxonomy_data:
        if "taxonomy" in data:
            taxonomy.update({data["key"]: read_taxonomy_values(data["taxonomy"])})
        else:
            taxonomy.update({data["key"]: asdict(_maybe_read(data))})
    return taxonomy
