"""Add ISO-3166-2 country subdivisions to geography table

Revision ID: 0064
Revises: 0063
Create Date: 2025-03-10 14:58:54.023942

"""

from typing import cast

import pycountry
from alembic import op
from pycountry.db import Country
from slugify import slugify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.models.dfce.geography import Geography

# revision identifiers, used by Alembic.
revision = "0064"
down_revision = "0063"
branch_labels = None
depends_on = None

# Taken from: https://github.com/pycountry/pycountry/blob/e74d49de784b47ab0bbb9ca22c0dc58122daa232/src/pycountry/databases/iso3166-1.json#L1828-L1833
vat = pycountry.countries.get(alpha_3="VAT")
vat_geography = Geography(
    display_value=getattr(vat, "name", "Holy See (Vatican City State)"),
    slug=slugify(getattr(vat, "name", "Holy See (Vatican City State)")),
    value=getattr(vat, "alpha_3", "VAT"),
    type="ISO-3166",
    parent_id=215,  # Other
)


def add_countries_pycountry(session: Session):
    for country in pycountry.countries:
        country = cast(Country, country)
        existing_country = (
            session.query(Geography).filter(Geography.value == country.alpha_3).first()
        )

        # if exists - update with new values
        if existing_country is not None:
            # check if the name and display value match
            name = getattr(country, "common_name", country.name)
            if existing_country.display_value != name:
                session.query(Geography).filter(
                    Geography.value == country.alpha_3
                ).update({"display_value": name})

            continue

    session.add(instance=vat_geography)
    session.commit()


def upgrade():
    Base = automap_base()
    bind = op.get_bind()
    Base.prepare(autoload_with=bind)

    session = Session(bind=bind)
    add_countries_pycountry(session)


def downgrade():
    pass
