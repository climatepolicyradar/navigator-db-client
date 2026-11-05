"""
Regression tests for the last_modified triggers on the link/child tables.

The flattened baseline migration created these triggers as BEFORE ... DELETE with
functions that `RETURN NEW` (NULL on DELETE), which silently cancelled deletes: the
DELETE statement succeeded with rowcount 0 and the rows stayed in place.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

TRIGGER_TABLES = [
    ("update_collection_last_modified", "collection_family"),
    ("update_family_last_modified", "family_event"),
    ("update_family_last_modified", "family_document"),
]


@pytest.fixture
def linked_rows(test_db: Session) -> Session:
    """A collection, family, link, family_event and family_document."""
    test_db.execute(
        text(
            """
            INSERT INTO collection (import_id, title, description, valid_metadata)
            VALUES ('C.1', 'c', 'd', '{}');
            INSERT INTO family (import_id, title, description, family_category)
            VALUES ('F.1', 'f', 'd', 'EXECUTIVE');
            INSERT INTO collection_family (collection_import_id, family_import_id)
            VALUES ('C.1', 'F.1');
            INSERT INTO physical_document (id, title) VALUES (1, 'doc');
            INSERT INTO family_document
                (family_import_id, physical_document_id, import_id, document_status,
                 valid_metadata)
            VALUES ('F.1', 1, 'D.1', 'CREATED', '{}');
            INSERT INTO family_event
                (import_id, title, date, event_type_name, family_import_id, status,
                 valid_metadata)
            VALUES ('E.1', 'e', now(), 'Passed/Approved', 'F.1', 'OK', '{}');
            """
        )
    )
    test_db.commit()
    return test_db


def _count(db: Session, table: str) -> int:
    return db.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def test_last_modified_triggers_are_after_triggers(test_db: Session):
    """BEFORE row triggers can cancel the triggering operation; these must be AFTER."""
    for trigger, table in TRIGGER_TABLES:
        definition = test_db.execute(
            text(
                """
                SELECT pg_get_triggerdef(oid) FROM pg_trigger
                WHERE tgname = :trigger AND tgrelid = CAST(:table AS regclass)
                """
            ),
            {"trigger": trigger, "table": f"public.{table}"},
        ).scalar_one()
        assert " AFTER " in definition, f"{trigger} on {table}: {definition}"


def test_delete_collection_family_removes_row(linked_rows: Session):
    result = linked_rows.execute(
        text(
            """
            DELETE FROM collection_family
            WHERE collection_import_id = 'C.1' AND family_import_id = 'F.1'
            """
        )
    )
    linked_rows.commit()

    assert result.rowcount == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert _count(linked_rows, "collection_family") == 0


def test_delete_family_event_removes_row(linked_rows: Session):
    result = linked_rows.execute(
        text("DELETE FROM family_event WHERE import_id = 'E.1'")
    )
    linked_rows.commit()

    assert result.rowcount == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert _count(linked_rows, "family_event") == 0


def test_delete_family_document_removes_row(linked_rows: Session):
    result = linked_rows.execute(
        text("DELETE FROM family_document WHERE import_id = 'D.1'")
    )
    linked_rows.commit()

    assert result.rowcount == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert _count(linked_rows, "family_document") == 0


def test_delete_still_touches_parent_last_modified(linked_rows: Session):
    """Fixing the trigger timing must not lose the behaviour it exists for."""
    before = linked_rows.execute(
        text("SELECT last_modified FROM family WHERE import_id = 'F.1'")
    ).scalar_one()
    linked_rows.execute(text("DELETE FROM family_event WHERE import_id = 'E.1'"))
    linked_rows.commit()
    after = linked_rows.execute(
        text("SELECT last_modified FROM family WHERE import_id = 'F.1'")
    ).scalar_one()

    # now() is transaction-start time, so the later transaction is strictly newer.
    assert after > before


def test_family_deletable_after_children_removed(linked_rows: Session):
    """The ForeignKeyViolation seen downstream: a family could not be deleted."""
    linked_rows.execute(
        text("DELETE FROM collection_family WHERE family_import_id = 'F.1'")
    )
    linked_rows.execute(text("DELETE FROM family_event WHERE family_import_id = 'F.1'"))
    linked_rows.execute(
        text("DELETE FROM family_document WHERE family_import_id = 'F.1'")
    )
    linked_rows.execute(text("DELETE FROM family WHERE import_id = 'F.1'"))
    linked_rows.commit()

    assert _count(linked_rows, "family") == 0
