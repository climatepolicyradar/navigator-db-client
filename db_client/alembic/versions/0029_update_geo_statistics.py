"""Update geo statistics

Revision ID: 0029
Revises: 0028
Create Date: 2024-02-26 17:37:27.110429

"""

import csv
from string import Template

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from db_client.utils import get_library_path

# revision identifiers, used by Alembic.
revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

UPDATE_COMMAND = Template(
    """
    UPDATE geo_statistics
    SET global_emissions_percent='$global_emissions_percent', climate_risk_index='$climate_risk_index'
    WHERE name=E'$name'
"""
)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "geo_statistics",
        "global_emissions_percent",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "geo_statistics",
        "climate_risk_index",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        type_=sa.Text(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###

    # Update with new values
    root = get_library_path()
    with open(
        f"{root}/alembic/versions/data/0029/geo_stats.csv", newline=""
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sql = UPDATE_COMMAND.substitute(
                name=row["name"].replace("'", "\\'"),
                global_emissions_percent=row["global_emissions_percent"],
                climate_risk_index=row["climate_risk_index"],
            )
            op.execute(sql)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "geo_statistics",
        "climate_risk_index",
        existing_type=sa.Text(),
        type_=postgresql.DOUBLE_PRECISION(precision=53),
        existing_nullable=True,
    )
    op.alter_column(
        "geo_statistics",
        "global_emissions_percent",
        existing_type=sa.Text(),
        type_=postgresql.DOUBLE_PRECISION(precision=53),
        existing_nullable=True,
    )
    # ### end Alembic commands ###
