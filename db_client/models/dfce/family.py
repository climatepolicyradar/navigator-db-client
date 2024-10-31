import logging
from datetime import datetime
from typing import Literal, Optional, cast

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from db_client.models.base import Base
from db_client.models.document import PhysicalDocument
from db_client.models.organisation import BaseModelEnum, Corpus

from .geography import Geography

_LOGGER = logging.getLogger(__name__)


class FamilyCategory(BaseModelEnum):
    """Family categories as understood in the context of law/policy."""

    EXECUTIVE = "Executive"
    LEGISLATIVE = "Legislative"
    UNFCCC = "UNFCCC"
    MCF = "MCF"


class Variant(Base):
    """
    The type of variant of a document within a family.

    Variants are described in the family/collection/doc notion page.
    Examples: "original language", "official translation", "unofficial translation.
    """

    __tablename__ = "variant"
    variant_name = sa.Column(sa.Text, primary_key=True)
    description = sa.Column(sa.Text, nullable=False)


class FamilyStatus(BaseModelEnum):
    """Family status to control visibility in the app."""

    CREATED = "Created"
    PUBLISHED = "Published"
    DELETED = "Deleted"


class Family(Base):
    """A representation of a group of documents that represent a single law/policy."""

    __tablename__ = "family"
    __allow_unmapped__ = True

    title = sa.Column(sa.Text, nullable=False)
    import_id = sa.Column(sa.Text, primary_key=True)
    description = sa.Column(sa.Text, nullable=False)
    family_category = sa.Column(sa.Enum(FamilyCategory), nullable=False)

    family_documents: list["FamilyDocument"] = relationship(
        "FamilyDocument",
        lazy="joined",
    )
    slugs: list["Slug"] = relationship(
        "Slug", lazy="joined", order_by="desc(Slug.created)"
    )
    # Define the relationship to Geography through the FamilyGeography link table
    geographies = relationship(
        "Geography",
        secondary="family_geography",
        primaryjoin="Family.import_id == FamilyGeography.family_import_id",
        secondaryjoin="Geography.id == FamilyGeography.geography_id",
        order_by="Geography.slug",
    )
    events: list["FamilyEvent"] = relationship(
        "FamilyEvent",
        lazy="joined",
        order_by="FamilyEvent.date",
    )
    created = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    last_modified = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    @hybrid_property
    def family_status(self) -> Literal[FamilyStatus]:  # type: ignore
        """Calculates the family status given its documents."""
        if not self.family_documents:
            return FamilyStatus.CREATED

        doc_states = [doc.document_status for doc in self.family_documents]
        if DocumentStatus.PUBLISHED in doc_states:
            return FamilyStatus.PUBLISHED
        if DocumentStatus.CREATED in doc_states:
            return FamilyStatus.CREATED
        # If we get here then all must be deleted
        return FamilyStatus.DELETED

    @family_status.expression
    def family_status(cls):
        is_published = (
            sa.select([sa.func.count(FamilyDocument.document_status)])
            .where(
                sa.and_(
                    FamilyDocument.family_import_id == cls.import_id,
                    FamilyDocument.document_status == DocumentStatus.PUBLISHED,
                )
            )
            .as_scalar()
        )

        is_created = (
            sa.select([sa.func.count(FamilyDocument.document_status)])
            .where(
                sa.and_(
                    FamilyDocument.family_import_id == cls.import_id,
                    FamilyDocument.document_status == DocumentStatus.CREATED,
                )
            )
            .as_scalar()
        )

        # DO NOT USE 'is None'!
        return sa.case(
            [
                (
                    cls.family_documents == None,  # noqa: E711
                    sa.literal_column(f"'{FamilyStatus.CREATED}'"),
                )
            ],
            else_=sa.case(
                [(is_published > 0, sa.literal_column(f"'{FamilyStatus.PUBLISHED}'"))],
                else_=sa.case(
                    [(is_created > 0, sa.literal_column(f"'{FamilyStatus.CREATED}'"))],
                    else_=sa.literal_column(f"'{FamilyStatus.DELETED}'"),
                ),
            ),
        ).label("family_status")

    @hybrid_property
    def published_date(self) -> Optional[datetime]:  # type: ignore
        """A date to use for filtering by published date."""
        if not self.events:
            return None

        date = None
        for event in self.events:
            event_meta = cast(dict, event.valid_metadata)
            _LOGGER.error(event_meta)
            if "datetime_event_name" not in event_meta:
                _LOGGER.error(event_meta)
                # return None

            datetime_event_name = event_meta["datetime_event_name"][0]
            if event.event_type_name == datetime_event_name:
                return cast(datetime, event.date)
            if date is None:
                date = cast(datetime, event.date)
            else:
                date = min(cast(datetime, event.date), date)
        return date

    @hybrid_property
    def last_updated_date(self) -> Optional[datetime]:
        """A "last updated" date to use during display of Family."""
        if not self.events:
            return None
        date = None
        for event in self.events:
            if date is None:
                date = cast(datetime, event.date)
            else:
                date = max(cast(datetime, event.date), date)
        return date


class DocumentStatus(BaseModelEnum):
    """FamilyDocument status to control visibility in the app."""

    CREATED = "Created"
    PUBLISHED = "Published"
    DELETED = "Deleted"


class FamilyDocument(Base):
    """A link between a Family and a PhysicalDocument."""

    __tablename__ = "family_document"
    __allow_unmapped__ = True

    family_import_id = sa.Column(sa.ForeignKey(Family.import_id), nullable=False)
    physical_document_id = sa.Column(
        sa.ForeignKey(PhysicalDocument.id),
        nullable=False,
        unique=True,
    )

    import_id = sa.Column(sa.Text, primary_key=True)
    variant_name = sa.Column(sa.ForeignKey(Variant.variant_name), nullable=True)
    document_status = sa.Column(
        sa.Enum(DocumentStatus), default=DocumentStatus.CREATED, nullable=False
    )
    created = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    last_modified = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    slugs: list["Slug"] = relationship(
        "Slug", lazy="joined", order_by="desc(Slug.created)"
    )
    physical_document: PhysicalDocument = relationship(
        PhysicalDocument,
        lazy="joined",
    )

    valid_metadata = sa.Column(postgresql.JSONB, nullable=False)


class FamilyGeography(Base):  # noqa: D101
    """Database model for a Family's Geographys"""

    __tablename__ = "family_geography"

    geography_id = sa.Column(sa.ForeignKey(Geography.id), nullable=False)
    family_import_id = sa.Column(sa.ForeignKey(Family.import_id), nullable=False)
    sa.PrimaryKeyConstraint(geography_id, family_import_id)


class Slug(Base):
    """An identifier for a Family of FamilyDocument to be used in URLs."""

    __tablename__ = "slug"
    __table_args__ = (
        sa.CheckConstraint(
            "num_nonnulls(family_import_id, family_document_import_id) = 1",
            name="must_reference_exactly_one_entity",
        ),
        sa.PrimaryKeyConstraint("name", name="pk_slug"),
    )

    name = sa.Column(sa.Text, primary_key=True)
    family_import_id = sa.Column(sa.ForeignKey(Family.import_id))
    family_document_import_id = sa.Column(sa.ForeignKey(FamilyDocument.import_id))
    created = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


class EventStatus(BaseModelEnum):
    """Event status to flag data issues from import."""

    OK = "Ok"
    # Duplicate means a single event was applied to multiple families. In this
    # case we will need to validate, remove unnecessary duplicates & create new
    # events through a data cleaning exercise.
    DUPLICATED = "Duplicated"


class FamilyEvent(Base):
    """An event associated with a Family timeline with optional link to a document."""

    __tablename__ = "family_event"

    import_id = sa.Column(sa.Text, primary_key=True)
    title = sa.Column(sa.Text, nullable=False)
    date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    event_type_name = sa.Column(sa.Text, nullable=False)
    family_import_id = sa.Column(sa.ForeignKey(Family.import_id), nullable=False)
    family_document_import_id = sa.Column(
        sa.ForeignKey(FamilyDocument.import_id),
        default=None,
        nullable=True,
    )
    status = sa.Column(sa.Enum(EventStatus), nullable=False)
    created = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    last_modified = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    valid_metadata = sa.Column(postgresql.JSONB, nullable=True)


class FamilyCorpus(Base):
    __tablename__ = "family_corpus"

    family_import_id = sa.Column(sa.ForeignKey(Family.import_id), nullable=False)
    corpus_import_id = sa.Column(sa.ForeignKey(Corpus.import_id), nullable=False)

    sa.PrimaryKeyConstraint(family_import_id)
