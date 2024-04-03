import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from db_client.models.base import Base
from db_client.models.dfce.family import Family


class FamilyMetadata(Base):
    """A set of metadata values linked to a Family."""

    __tablename__ = "family_metadata"

    family_import_id = sa.Column(sa.ForeignKey(Family.import_id))

    value = sa.Column(postgresql.JSONB, nullable=False)

    sa.PrimaryKeyConstraint(family_import_id)
