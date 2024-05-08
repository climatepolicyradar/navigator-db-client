from typing import Sequence

from sqlalchemy.orm import Session

from db_client.models.dfce.family import Family, FamilyCorpus
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.organisation.corpus import Corpus, CorpusType

MetadataValidationResult = Sequence[str]


def validate_family_metadata(db: Session, family: Family) -> MetadataValidationResult:
    """Validates the Family's metadata against its Corpus' Taxonomy.

    :param Session db: The db connection session.
    :param Family family: The family to validate.
    :return MetadataValidationResult: A list of errors or an empty list meaning ok
    """

    taxonomy, metadata = (
        db.query(CorpusType.valid_metadata, FamilyMetadata.value)
        .join(Corpus, CorpusType.name == Corpus.corpus_type_name)
        .join(FamilyCorpus, FamilyCorpus.corpus_import_id == Corpus.import_id)
        .join(Family, family.import_id == FamilyCorpus.family_import_id)
        .join(FamilyMetadata, FamilyMetadata.family_import_id == family.import_id)
        .filter(Family.import_id == family.import_id)
    )

    return [taxonomy, metadata]
