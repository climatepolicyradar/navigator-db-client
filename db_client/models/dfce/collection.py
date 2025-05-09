import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from db_client.models.base import Base
from db_client.models.dfce.family import Family
from db_client.models.organisation.users import Organisation


class Collection(Base):
    """A collection of document families."""

    __tablename__ = "collection"

    import_id = sa.Column(sa.Text, primary_key=True)
    title = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    valid_metadata = sa.Column(postgresql.JSONB, nullable=False)
    created = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    last_modified = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )


class CollectionFamily(Base):
    """Relationship table connecting collections to families."""

    __tablename__ = "collection_family"

    collection_import_id = sa.Column(
        sa.ForeignKey(Collection.import_id), nullable=False
    )
    family_import_id = sa.Column(sa.ForeignKey(Family.import_id), nullable=False)
    sa.PrimaryKeyConstraint(collection_import_id, family_import_id)


class CollectionOrganisation(Base):
    """Relationship representing ownership of a collection by an organisation."""

    __tablename__ = "collection_organisation"

    collection_import_id = sa.Column(
        sa.ForeignKey(Collection.import_id), nullable=False
    )
    organisation_id = sa.Column(sa.ForeignKey(Organisation.id), nullable=False)

    sa.PrimaryKeyConstraint(collection_import_id)
