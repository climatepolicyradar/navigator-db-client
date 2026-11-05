"""
Regression tests for schema objects the flattened baseline migration dropped.

Raw SQL inserts (not going through the ORM, which supplies these values itself)
must get the same defaults the pre-flatten migration chain provided.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def test_family_concepts_defaults_to_empty_array(test_db: Session):
    test_db.execute(
        text(
            """
            INSERT INTO family (import_id, title, description, family_category)
            VALUES ('F.1', 'f', 'd', 'EXECUTIVE')
            """
        )
    )
    concepts = test_db.execute(
        text("SELECT concepts FROM family WHERE import_id = 'F.1'")
    ).scalar_one()

    assert concepts == []


def test_physical_document_language_source_and_visible_defaults(test_db: Session):
    test_db.execute(text("INSERT INTO physical_document (id, title) VALUES (1, 'doc')"))
    language_id = test_db.execute(text("SELECT id FROM language LIMIT 1")).scalar_one()
    test_db.execute(
        text(
            """
            INSERT INTO physical_document_language (language_id, document_id)
            VALUES (:language_id, 1)
            """
        ),
        {"language_id": language_id},
    )
    row = test_db.execute(
        text("SELECT source::text, visible FROM physical_document_language")
    ).one()

    assert row.source == "MODEL"
    assert row.visible is False


def test_familystatus_enum_exists(test_db: Session):
    labels = test_db.execute(
        text("SELECT unnest(enum_range(NULL::familystatus))::text")
    ).scalars()

    assert list(labels) == ["CREATED", "PUBLISHED", "DELETED"]
