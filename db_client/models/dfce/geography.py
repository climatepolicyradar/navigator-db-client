import sqlalchemy as sa

from db_client.models.base import Base

GEO_NONE = "XAA"
GEO_INTERNATIONAL = "XAB"

GEO_OTHER = "Other"
CPR_DEFINED_GEOS = {GEO_NONE: "No Geography", GEO_INTERNATIONAL: "International"}


class Geography(Base):  # noqa: D101
    """Database model for Geography"""

    __tablename__ = "geography"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    # to display to end-users
    display_value = sa.Column(sa.Text, nullable=False)
    slug = sa.Column(sa.Text, nullable=False, unique=True, index=True)
    # e.g. ISO code, World Bank, etc - not necessarily for display
    # non-unique, as some unrecognised territories might share the same code, e.g.
    # at the time of writing, "Sahrawi Republic" and "Western Sahara" both share "ESH"
    value = sa.Column(sa.Text)
    type = sa.Column(sa.Text)
    parent_id = sa.Column(sa.ForeignKey("geography.id"))


class GeoStatistics(Base):
    """Database model for statistics based on geography."""

    __tablename__ = "geo_statistics"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    geography_id = sa.Column(
        sa.Integer(), sa.ForeignKey("geography.id"), nullable=False
    )
    legislative_process = sa.Column(sa.Text(), nullable=False)
    federal = sa.Column(sa.Boolean(), nullable=False)
    federal_details = sa.Column(sa.Text(), nullable=False)
    political_groups = sa.Column(sa.Text(), nullable=False)
    global_emissions_percent = sa.Column(sa.Text(), nullable=True)
    climate_risk_index = sa.Column(sa.Text(), nullable=True)
    worldbank_income_group = sa.Column(sa.Text(), nullable=False)
    visibility_status = sa.Column(sa.Text(), nullable=False)
