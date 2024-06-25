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

    NOTE: That the taxonomy is also validated. This is because the
    Taxonomy is stored in the database and can be mutated independently
    of the Family's metadata.

    :param Session db: The db connection session.
    :param Family family: The family to validate.
    :raises TypeError: If the Taxonomy is invalid.
    :raises ValidationError: If the Taxonomy values are invalid.
    :return Optional[MetadataValidationResult]: A list of errors or None
        if the metadata is valid.
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

    errors = validate_metadata(taxonomy_entries, family_metadata)

    # TODO: validate family_metadata against taxonomy
    return errors if len(errors) > 0 else None


def validate_metadata(taxonomy_entries, family_metadata) -> MetadataValidationErrors:
    """_summary_

    :param _type_ taxonomy_entries: _description_
    :param _type_ family_metadata: _description_
    :return MetadataValidationErrors: _description_
    """
    errors = []
    metadata_keys = set(family_metadata.keys())
    taxonomy_keys = set(taxonomy_entries.keys())
    missing_keys = taxonomy_keys - metadata_keys
    if len(missing_keys) > 0:
        errors.append(f"Missing metadata keys: {missing_keys}")
    extra_keys = metadata_keys - taxonomy_keys
    if len(extra_keys) > 0:
        errors.append(f"Extra metadata keys: {extra_keys}")

    # Validate the metadata values
    for key, value_list in family_metadata.items():
        if key not in taxonomy_entries:
            continue  # We've already checked for missing keys
        taxonomy_entry = taxonomy_entries[key]
        if not isinstance(value_list, list):
            errors.append(
                f"Invalid value '{value_list}' for metadata key '{key}' expected list."
            )
            continue

        if not taxonomy_entry.allow_any:
            if not all(item in taxonomy_entry.allowed_values for item in value_list):
                errors.append(f"Invalid value '{value_list}' for metadata key '{key}'")
                continue

        if not taxonomy_entry.allow_blanks and value_list == []:
            errors.append(f"Blank value for metadata key '{key}'")

    return errors


def build_valid_taxonomy(taxonomy: Mapping) -> Mapping[str, TaxonomyEntry]:
    """Takes the taxonomy from the database and builds a dictionary of TaxonomyEntry objects, used for validation.

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

        if not isinstance(values, dict):
            raise TypeError(f"Taxonomy entry for '{key}' is not a dictionary")

        # We rely on pydantic to validate the values here
        taxonomy_entries[key] = TaxonomyEntry(**values)

    return taxonomy_entries
