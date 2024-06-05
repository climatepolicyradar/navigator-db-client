from typing import Any, Sequence

from sqlalchemy.orm import Session

from db_client.models.dfce.family import Family, FamilyCorpus
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.dfce.taxonomy_entry import TaxonomyEntry
from db_client.models.organisation.corpus import Corpus, CorpusType

MetadataValidationResult = Sequence[str]

# TODO use the MetadataValidationResult as the return value
# class MetadataValidationError(Exception):
#     """An Error that occurs when validating metadata"""

#     @property
#     def message(self) -> str:
#         """
#         Returns the message for the exception.

#         :return str: The message string.
#         """
#         return self.args[0] if len(self.args) > 0 else "<no message>"


def validate_taxonomy(taxonomy: dict[str, Any]) -> MetadataValidationResult:
    """Validates the Taxonomy.

    :param dict[str, Any] taxonomy: The taxonomy to validate.
    """
    result = []
    for entry in taxonomy:
        if "node" in entry:
            node = entry["node"]
            if "name" not in node:
                result.append("Taxonomy entry is missing 'name' field")
        else:
            result.append("Taxonomy entry is missing 'node' field")
    return result


def validate_family_metadata(db: Session, family: Family):
    """Validates the Family's metadata against its Corpus' Taxonomy.

    :param Session db: The db connection session.
    :param Family family: The family to validate.
    :return MetadataValidationResult: A list of errors or an empty list meaning ok
    """

    # Retrieve the Taxonomy and the Family's metadata
    corpus_type, metadata = (
        db.query(CorpusType, FamilyMetadata)
        .join(Corpus, CorpusType.name == Corpus.corpus_type_name)
        .join(FamilyCorpus, FamilyCorpus.corpus_import_id == Corpus.import_id)
        .join(Family, family.import_id == FamilyCorpus.family_import_id)
        .join(FamilyMetadata, FamilyMetadata.family_import_id == family.import_id)
        .filter(Family.import_id == family.import_id)
        .one()
    )

    taxonomy = corpus_type.valid_metadata
    if type(taxonomy) is not list:
        raise TypeError("Taxonomy is not a list")
    # Will throw a TypeError if the taxonomy is not a dict.
    taxonomy_entries = [TaxonomyEntry(**list(entry.values())[0]) for entry in taxonomy]
    print(taxonomy_entries)

    # TODO: validate_taxonomy()
    family_metadata = metadata.value

    # TODO: validate family_metadata against taxonomy
    return [taxonomy, family_metadata]
