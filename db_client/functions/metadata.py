from typing import Mapping, Optional, Sequence

from sqlalchemy.orm import Session

from db_client.functions.corpus_helpers import (
    get_entity_specific_taxonomy,
    get_taxonomy_from_corpus,
)
from db_client.models.dfce.taxonomy_entry import TaxonomyEntry

MetadataValidationErrors = Sequence[str]


def validate_family_metadata(
    db: Session, corpus_id: str, metadata
) -> Optional[MetadataValidationErrors]:
    """Validates the Family's metadata against its Corpus' Taxonomy.

    NOTE: That the taxonomy is also validated. This is because the
    Taxonomy is stored in the database and can be mutated independently
    of the Family's metadata.

    :param Session db: The Session to query.
    :param str corpus_id: The corpus import ID to retrieve the taxonomy
        for.
    :param dict metadata: The family metadata to validate.
    :return Optional[MetadataValidationResult]: A list of errors or None
        if the metadata is valid.
    """
    taxonomy = get_taxonomy_from_corpus(db, corpus_id)
    if taxonomy is None:
        raise TypeError("No taxonomy found for corpus")

    # Make sure we only get the family taxonomy keys.
    # TODO: When we move the family schema under _family we can consolidate these entity
    # specific validation functions.
    taxonomy = {
        k: v for (k, v) in taxonomy.items() if k not in ["_document", "event_type"]
    }
    return _validate_metadata_against_taxonomy(taxonomy, metadata)


def validate_document_metadata(
    db, corpus_id: str, metadata
) -> Optional[MetadataValidationErrors]:
    """Validates the Document's metadata against its Corpus' Taxonomy.

    NOTE: That the taxonomy is also validated. This is because the
    Taxonomy is stored in the database and can be mutated independently
    of the Family's metadata.

    :param Session db: The Session to query.
    :param str corpus_id: The corpus import ID to retrieve the taxonomy
        for.
    :param dict metadata: The document metadata to validate.
    :return Optional[MetadataValidationResult]: A list of errors or None
        if the metadata is valid.
    """
    taxonomy = get_taxonomy_from_corpus(db, corpus_id)
    if taxonomy is None:
        raise TypeError("No taxonomy found for corpus")

    # Make sure we only get the document taxonomy keys.
    # TODO: When we move the family schema under _family we can consolidate these entity
    # specific validation functions.
    taxonomy = get_entity_specific_taxonomy(taxonomy, "_document")
    return _validate_metadata_against_taxonomy(taxonomy, metadata)


def _validate_metadata_against_taxonomy(taxonomy, metadata):
    """Build the Corpus taxonomy for the entity & validate against it.

    :param dict taxonomy: The Corpus taxonomy to validate against.
    :param dict metadata: The metadata to validate.
    :raises TypeError: If the Taxonomy is invalid.
    :return Optional[MetadataValidationResult]: A list of errors or None
        if the metadata is valid.
    """
    try:
        taxonomy_entries = build_valid_taxonomy(taxonomy)
    except TypeError as e:
        # Wrap any TypeError in a more general error
        raise TypeError("Bad Taxonomy data in database") from e

    errors = validate_metadata(taxonomy_entries, metadata)
    return errors if len(errors) > 0 else None


def validate_metadata(
    taxonomy_entries: Mapping[str, TaxonomyEntry], metadata: Mapping
) -> MetadataValidationErrors:
    """Validates the metadata against the taxonomy.

    :param _type_ taxonomy_entries: The built entries from the
        CorpusType.valid_metadata.
    :param _type_ metadata: The metadata to validate.
    :return MetadataValidationErrors: a list of errors if the metadata
        is invalid.
    """
    errors = []
    metadata_keys = set(metadata.keys())
    taxonomy_keys = set(taxonomy_entries.keys())
    missing_keys = taxonomy_keys - metadata_keys
    if len(missing_keys) > 0:
        errors.append(f"Missing metadata keys: {missing_keys}")
    extra_keys = metadata_keys - taxonomy_keys
    if len(extra_keys) > 0:
        errors.append(f"Extra metadata keys: {extra_keys}")

    # Validate the metadata values
    for key, value_list in metadata.items():
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
    """Build valid taxonomy used to validate metadata against.

    Takes the taxonomy from the database and builds a dictionary of
    TaxonomyEntry objects, used for validation.

    :param Sequence taxonomy: From the database model
        CorpusType.valid_metadata and potentially filtered by entity key
    :raises TypeError: If the taxonomy is not a list.
    :raises TypeError: If the taxonomy entry is not a dictionary.
    :raises TypeError: If the values within the taxonomy entry are not
        dictionaries.
    :return Mapping[str, TaxonomyEntry]: a dictionary of TaxonomyEntry
        objects (contains property constraints) keyed by the taxonomy
        entry name (property).
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
