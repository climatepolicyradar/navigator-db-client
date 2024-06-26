"""Remove FamilyEventType table

Revision ID: 0038
Revises: 0037
Create Date: 2024-06-27 11:18:04.834908

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from db_client.utils import get_library_path

Base = automap_base()

# revision identifiers, used by Alembic.
revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def _populate_event_type(db: Session) -> None:
    """Populates the family_event_type table with pre-defined data."""

    with open(
        f"{get_library_path()}/alembic/versions/data/0037/event_type_data.json"
    ) as event_type_file:
        event_type_data = json.load(event_type_file)

        query = text(
            "insert into family_event_type (name, description) values "
            "(:name, :description)"
        )
        db.execute(query, params=event_type_data)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "fk_family_event__event_type_name__family_event_type",
        "family_event",
        type_="foreignkey",
    )
    op.drop_table("family_event_type")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "family_event_type",
        sa.Column("name", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("description", sa.TEXT(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("name", name="pk_family_event_type"),
    )

    # Repopulate table with initial event type names.
    bind = op.get_bind()
    Base.prepare(autoload_with=bind)

    session = Session(bind=bind)
    _populate_event_type(session)

    op.create_foreign_key(
        "fk_family_event__event_type_name__family_event_type",
        "family_event",
        "family_event_type",
        ["event_type_name"],
        ["name"],
    )
    # ### end Alembic commands ###
