""" DO NOT CHANGE THIS FILE """

import json

from sqlalchemy.orm import Session

from db_client.models.document.physical_document import Language
from db_client.utils import get_library_path

from .utils import has_rows, load_list


def _populate_language(db: Session) -> None:
    """Populates the langauge table with pre-defined data."""

    if has_rows(db, Language):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/language_data.json"
    ) as language_file:
        language_data = json.load(language_file)
        load_list(db, Language, language_data)
