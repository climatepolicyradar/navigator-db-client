import json

from sqlalchemy.orm import Session

from db_client.models.law_policy import FamilyEventType
from db_client.utils import get_library_path
from .utils import has_rows, load_list


def populate_event_type(db: Session) -> None:
    """Populates the family_event_type table with pre-defined data."""

    if has_rows(db, FamilyEventType):
        return

    with open(
        f"{get_library_path()}/data_migrations/data/law_policy/event_type_data.json"
    ) as event_type_file:
        event_type_data = json.load(event_type_file)
        load_list(db, FamilyEventType, event_type_data)
