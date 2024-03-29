import json

from sqlalchemy.orm import Session

from db_client.models.dfce.family import Variant
from db_client.utils import get_library_path

from .utils import has_rows, load_list


def populate_document_variant(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, Variant):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/document_variant_data.json"
    ) as document_variant_file:
        document_variant_data = json.load(document_variant_file)
        load_list(db, Variant, document_variant_data)
