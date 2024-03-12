import json

from sqlalchemy.orm import Session

from db_client.models.law_policy import FamilyDocumentRole
from db_client.utils import get_library_path

from .utils import has_rows, load_list


def populate_document_role(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, FamilyDocumentRole):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/document_role_data.json"
    ) as document_role_file:
        document_role_data = json.load(document_role_file)
        load_list(db, FamilyDocumentRole, document_role_data)
