from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from db_client.models.base import Base
from db_client.models.dfce.family import Family


class Concept(Base):
    """
    This is a concept model from the knowledge graph project.
    @see: https://github.com/climatepolicyradar/knowledge-graph/blob/main/src/concept.py
    """

    __tablename__ = "concept"

    id = Column(String, primary_key=True)
    preferred_label = Column(String, nullable=False)
    alternative_labels = Column(ARRAY(String), nullable=True)
    negative_labels = Column(ARRAY(String), nullable=True)
    description = Column(Text, nullable=True)
    wikibase_id = Column(String, nullable=True)
    subconcept_of = Column(ARRAY(String), nullable=True)
    has_subconcept = Column(ARRAY(String), nullable=True)
    related_concepts = Column(ARRAY(String), nullable=True)
    definition = Column(Text, nullable=True)

    families = relationship(
        "Family",
        secondary="family_concept",
        primaryjoin="Concept.id == FamilyConcept.concept_id",
        secondaryjoin="Family.import_id == FamilyConcept.family_import_id",
        back_populates="concepts",
    )

    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_modified = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class FamilyConcept(Base):
    """Database model for a Family's Concepts"""

    __tablename__ = "family_concept"

    concept_id = Column(ForeignKey(Concept.id), nullable=False)
    family_import_id = Column(ForeignKey(Family.import_id), nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_modified = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    PrimaryKeyConstraint(concept_id, family_import_id)
