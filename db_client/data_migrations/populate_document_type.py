import json

from sqlalchemy.orm import Session

from db_client.data_migrations.utils import has_rows, load_list_idempotent
from db_client.models.dfce.family import FamilyDocumentType
from db_client.utils import get_library_path


def populate_document_type(db: Session) -> None:
    """Populates the document_type table with pre-defined data."""

    if has_rows(db, FamilyDocumentType):
        return

    # This is no longer fixed but additive,
    # meaning we will add anything here that is not present in the table

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/document_type_data.json"
    ) as submission_type_file:
        document_type_data = json.load(submission_type_file)
        load_list_idempotent(
            db, FamilyDocumentType, FamilyDocumentType.name, "name", document_type_data
        )

    with open(
        f"{get_library_path()}/data_migrations/data/unf3c/submission_type_data.json"
    ) as submission_type_file:
        submission_type_data = json.load(submission_type_file)
        document_type_data = [
            {"name": e["name"], "description": e["name"]} for e in submission_type_data
        ]
        load_list_idempotent(
            db, FamilyDocumentType, FamilyDocumentType.name, "name", document_type_data
        )
