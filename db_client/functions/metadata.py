from typing import Mapping, Optional, Sequence

from sqlalchemy.orm import Session

from db_client.models.dfce.family import Family, FamilyCorpus
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.dfce.taxonomy_entry import TaxonomyEntry
from db_client.models.organisation.corpus import Corpus, CorpusType

MetadataValidationErrors = Sequence[str]


def validate_family_metadata(
    db: Session, family: Family
) -> Optional[MetadataValidationErrors]:
    """Validates the Family's metadata against its Corpus' Taxonomy.

    NOTE: That the taxonomy is also validated. This is because the Taxonomy is stored in the database and can be mutated independently of the Family's metadata.

    :param Session db: The db connection session.
    :param Family family: The family to validate.
    :raises TypeError: If the Taxonomy is invalid.
    :raises ValidationError: If the Taxonomy values are invalid.
    :return Optional[MetadataValidationResult]: A list of errors or None if the metadata is valid.
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
    try:
        taxonomy_entries = build_valid_taxonomy(taxonomy)
    except TypeError as e:
        # Wrap any TypeError in a more general error
        raise TypeError("Bad Taxonomy data in database") from e

    family_metadata = metadata.value

    errors = []
    metadata_keys = set(family_metadata.keys())
    taxonomy_keys = set(taxonomy_entries.keys())
    missing_keys = taxonomy_keys - metadata_keys
    if len(missing_keys) > 0:
        errors.append(f"Missing metadata keys: {missing_keys}")
    extra_keys = metadata_keys - taxonomy_keys
    if len(extra_keys) > 0:
        errors.append(f"Extra metadata keys: {extra_keys}")

    # TODO: validate family_metadata against taxonomy
    return errors if len(errors) > 0 else None


def build_valid_taxonomy(taxonomy: Mapping) -> Mapping[str, TaxonomyEntry]:
    """_summary_

    :param Sequence taxonomy: From the database model CorpusType.valid_metadata
    :raises TypeError: If the taxonomy is not a list.
    :raises TypeError: If the taxonomy entry is not a dictionary.
    :raises TypeError: If the values within the taxonomy entry are not dictionaries.
    :return Mapping[str, TaxonomyEntry]: a dictionary of TaxonomyEntry objects (contains property constraints) keyed by the taxonomy entry name (property).
    """
    if not isinstance(taxonomy, dict):
        raise TypeError("Taxonomy is not a dictionary")

    taxonomy_entries: Mapping[str, TaxonomyEntry] = {}
    for key, values in taxonomy.items():

        # values = list(entry.values())[0]
        if not isinstance(values, dict):
            raise TypeError(f"Taxonomy entry for '{key}' is not a dictionary")

        # We rely on pydantic to validate the values here
        taxonomy_entries[key] = TaxonomyEntry(**values)

    return taxonomy_entries
