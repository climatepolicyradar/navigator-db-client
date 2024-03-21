import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from db_client.models.base import Base
from db_client.models.dfce.family import Family
from db_client.models.organisation.users import Organisation


# TODO: Remove
class MetadataTaxonomy(Base):
    """A description of metadata taxonomies in terms of valid keys & values."""

    __tablename__ = "metadata_taxonomy"

    id = sa.Column(sa.Integer, primary_key=True)
    description = sa.Column(sa.Text, nullable=False)
    valid_metadata = sa.Column(postgresql.JSONB, nullable=False)


class FamilyMetadata(Base):
    """A set of metadata values linked to a Family."""

    __tablename__ = "family_metadata"

    family_import_id = sa.Column(sa.ForeignKey(Family.import_id))

    # TODO - remove as it can be derived from the Family's corpus
    taxonomy_id = sa.Column(sa.ForeignKey(MetadataTaxonomy.id))

    value = sa.Column(postgresql.JSONB, nullable=False)

    sa.PrimaryKeyConstraint(family_import_id, taxonomy_id)


# TODO: Remove
class MetadataOrganisation(Base):
    """A link from an Organisation to their metadata taxonomy."""

    __tablename__ = "metadata_organisation"

    taxonomy_id = sa.Column(sa.ForeignKey(MetadataTaxonomy.id), nullable=False)
    organisation_id = sa.Column(sa.ForeignKey(Organisation.id))

    sa.PrimaryKeyConstraint(organisation_id)
