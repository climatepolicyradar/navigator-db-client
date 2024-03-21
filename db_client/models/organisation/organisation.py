import sqlalchemy as sa

from db_client.models.base import Base


class Organisation(Base):
    """Table of organisations to which admin users may belong."""

    __tablename__ = "organisation"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    description = sa.Column(sa.String)
    organisation_type = sa.Column(sa.String)
