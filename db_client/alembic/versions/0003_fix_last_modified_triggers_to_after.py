"""Restore AFTER last-modified triggers (fix silently cancelled deletes)

The flattened baseline (0001) recreated the `update_family_last_modified` triggers
(on family_document and family_event) and `update_collection_last_modified` (on
collection_family) as BEFORE INSERT OR UPDATE OR DELETE. The trigger functions end
with `RETURN NEW`, which is NULL on DELETE, and a BEFORE row trigger returning NULL
silently cancels the operation. Deletes on those tables therefore affected 0 rows.

The pre-flatten chain had already fixed this in old migration 0025 ("Fixed event
trigger that was preventing event deletion") by making these triggers AFTER. This
migration restores that behaviour.

The trigger functions are also changed to `RETURN COALESCE(NEW, OLD)` so that they
are safe even if someone makes them BEFORE triggers again. For AFTER triggers the
return value is ignored, so this does not change behaviour otherwise.

The migration is idempotent: databases that were created from the old chain (and
re-stamped) already have AFTER triggers, and DROP TRIGGER IF EXISTS / CREATE OR
REPLACE make it a no-op for them.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-04

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

# (trigger name, table, function)
TRIGGERS = [
    (
        "update_family_last_modified",
        "family_document",
        "update_2_family_last_modified",
    ),
    ("update_family_last_modified", "family_event", "update_2_family_last_modified"),
    (
        "update_collection_last_modified",
        "collection_family",
        "update_2_collection_last_modified",
    ),
]


def _function_sql(name: str, table: str, key_column: str, return_expr: str) -> str:
    # Identifiers come from the hardcoded TRIGGERS constants, not user input.
    return f"""
    CREATE OR REPLACE FUNCTION public.{name}() RETURNS TRIGGER AS $$
    BEGIN
        if tg_op = 'DELETE' then
            UPDATE {table}
            SET last_modified = NOW()
            WHERE import_id = OLD.{key_column};
        else
            UPDATE {table}
            SET last_modified = NOW()
            WHERE import_id = NEW.{key_column};
        end if;
        RETURN {return_expr};
    END;
    $$ language 'plpgsql'
    """  # nosec B608


def _recreate_triggers(timing: str) -> None:
    for trigger, table, function in TRIGGERS:
        op.execute(f"DROP TRIGGER IF EXISTS {trigger} ON public.{table}")
        op.execute(
            f"""
            CREATE TRIGGER {trigger}
            {timing} INSERT OR UPDATE OR DELETE ON public.{table}
            FOR EACH ROW
            EXECUTE PROCEDURE public.{function}()
            """
        )


def upgrade():
    op.execute(
        _function_sql(
            "update_2_family_last_modified",
            "family",
            "family_import_id",
            "COALESCE(NEW, OLD)",
        )
    )
    op.execute(
        _function_sql(
            "update_2_collection_last_modified",
            "collection",
            "collection_import_id",
            "COALESCE(NEW, OLD)",
        )
    )
    _recreate_triggers("AFTER")


def downgrade():
    # Faithfully restores the 0002 state, which includes the delete-cancelling bug.
    op.execute(
        _function_sql(
            "update_2_family_last_modified", "family", "family_import_id", "NEW"
        )
    )
    op.execute(
        _function_sql(
            "update_2_collection_last_modified",
            "collection",
            "collection_import_id",
            "NEW",
        )
    )
    _recreate_triggers("BEFORE")
