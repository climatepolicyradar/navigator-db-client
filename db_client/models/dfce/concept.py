from pydantic import BaseModel, ValidationError
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates

from db_client.models.base import Base
from db_client.models.dfce.family import Family


class ExternalIds(BaseModel):
    source: str
    id: str


class Concept(Base):
    """
    This is a concept model from the knowledge graph project.
    @see: https://github.com/climatepolicyradar/knowledge-graph/blob/main/src/concept.py
    """

    __tablename__ = "concept"

    id = Column(String, primary_key=True)
    # This is used for any other ids e.g. wordpress, wikidata, etc.
    # The shape of this should be { "source": "climatecasechart.com/wp-json/wp/v2", "id": "case_category/415" }
    ids = Column(JSONB, nullable=False, default=list)
    preferred_label = Column(String, nullable=False)
    alternative_labels = Column(ARRAY(String), nullable=True)
    negative_labels = Column(ARRAY(String), nullable=True)
    description = Column(Text, nullable=True)
    wikibase_id = Column(String, nullable=True)
    subconcept_of = Column(ARRAY(String), nullable=True)
    has_subconcept = Column(ARRAY(String), nullable=True)
    related_concepts = Column(ARRAY(String), nullable=True)
    definition = Column(Text, nullable=True)

    @validates("ids")
    def validate_ids(self, key, value):
        if value is None:
            return value
        try:
            [ExternalIds.model_validate(item) for item in value]
        except ValidationError as e:
            raise ValueError(
                "ids should be a list[{ 'source': str, 'id': str }]"
            ) from e
        return value

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
    relation = Column(String, nullable=False)

    # We don't base this on a DB enum as we will want to update it on regular intervals
    @validates("relation")
    def validate_relation(self, key, value):
        valid_relations = ["author"]
        if value not in valid_relations:
            raise ValueError(f"relation must be one of {valid_relations}")
        return value

    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_modified = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    PrimaryKeyConstraint(concept_id, family_import_id)
