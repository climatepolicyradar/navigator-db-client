"""Add ISO-3166-2 country subdivisions to geography table

Revision ID: 0062
Revises: 0061
Create Date: 2025-03-10 14:58:54.023942

"""

from typing import cast

import pycountry
from alembic import op
from pycountry.db import Subdivision
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.models.dfce.geography import Geography

# revision identifiers, used by Alembic.
revision = "0062"
down_revision = "0061"
branch_labels = None
depends_on = None


def add_country_subdivisions_from_pycountry(session: Session):
    country_subdivisions = []
    for subdivision in pycountry.subdivisions:
        subdivision = cast(Subdivision, subdivision)
        # if it exists, skip
        existing_subdivision = (
            session.query(Geography).filter(Geography.value == subdivision.code).first()
        )
        if existing_subdivision is not None:
            print(f"Subdivision already exists: {subdivision.name}, {subdivision.code}")
            continue
        # if it does not have a parent, skip
        # trunk-ignore(pyright/reportGeneralTypeIssues)
        parent_country_alpha_3 = subdivision.country.alpha_3
        parent = (
            session.query(Geography)
            .filter(Geography.value == parent_country_alpha_3)
            .first()
        )
        if parent is None:
            # No parent found for {subdivision.name}, {subdivision.code}, {parent_country_alpha_3}
            continue

        country_subdivisions.append(
            Geography(
                display_value=subdivision.name,
                slug=subdivision.code.lower(),
                value=subdivision.code,
                type="ISO-3166-2",
                parent_id=parent.id if parent else None,
            )
        )

    session.add_all(country_subdivisions)
    session.commit()


def upgrade():
    Base = automap_base()
    bind = op.get_bind()
    Base.prepare(autoload_with=bind)

    session = Session(bind=bind)
    add_country_subdivisions_from_pycountry(session)


def downgrade():
    Base = automap_base()
    bind = op.get_bind()
    Base.prepare(autoload_with=bind)

    session = Session(bind=bind)

    iso_3166_2_subdivisions = (
        session.query(Geography).filter(Geography.type == "ISO-3166-2").all()
    )
    for subdivision in iso_3166_2_subdivisions:
        session.delete(subdivision)
    session.commit()
