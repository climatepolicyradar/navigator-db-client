import logging
from typing import Mapping, Optional, Sequence, Union

from sqlalchemy.orm import Session

from db_client.functions.corpus_helpers import (
    TaxonomyData,
    TaxonomyDataEntry,
    get_entity_specific_taxonomy,
    get_taxonomy_from_corpus,
)
from db_client.models.dfce.taxonomy_entry import (
    EntitySpecificTaxonomyKeys,
    TaxonomyEntry,
)

MetadataValidationErrors = Sequence[str]
_LOGGER = logging.getLogger(__name__)


def validate_metadata(
    db: Session,
    corpus_id: str,
    metadata: TaxonomyDataEntry,
    entity_key: Optional[str] = None,
) -> Optional[MetadataValidationErrors]:
    """Validates the metadata against its Corpus' Taxonomy.

    NOTE: That the taxonomy is also validated. This is because the
    Taxonomy is stored in the database and can be mutated independently
    of the metadata.

    :param Session db: The Session to query.
    :param str corpus_id: The corpus import ID to retrieve the taxonomy
        for.
    :param TaxonomyDataEntry metadata: The event metadata to validate.
    :param EntitySpecificTaxonomyKeys _entity_key: The entity specific
        key to filter taxonomy by.
    :return Optional[MetadataValidationResult]: A list of errors or None
        if the metadata is valid.
    """
    taxonomy = get_taxonomy_from_corpus(db, corpus_id)
    if taxonomy is None:
        raise TypeError("No taxonomy found for corpus")

    # Make sure we only get the entity specific taxonomy keys.
    if entity_key is None:
        # Assume that we are validating family metadata.
        taxonomy = {
            k: v
            for (k, v) in taxonomy.items()
            if k
            not in [
                EntitySpecificTaxonomyKeys.DOCUMENT.value,
                EntitySpecificTaxonomyKeys.EVENT.value,
            ]
        }
    else:
        taxonomy = get_entity_specific_taxonomy(taxonomy, entity_key)
    return validate_metadata_against_taxonomy(taxonomy, metadata)


def validate_metadata_against_taxonomy(
    taxonomy: Union[TaxonomyData, TaxonomyDataEntry], metadata: TaxonomyDataEntry
) -> Optional[MetadataValidationErrors]:
    """Build the Corpus taxonomy for the entity & validate against it.

    :param TaxonomyDataEntry taxonomy: The Corpus taxonomy to validate against.
    :param TaxonomyDataEntry metadata: The metadata to validate.
    :raises TypeError: If the Taxonomy is invalid.
    :return Optional[MetadataValidationResult]: A list of errors or None
        if the metadata is valid.
    """
    try:
        taxonomy_entries = build_valid_taxonomy(taxonomy, metadata)
    except TypeError as e:
        _LOGGER.error(e)
        # Wrap any TypeError in a more general error
        raise TypeError("Bad Taxonomy data in database") from e

    errors = _validate_metadata(taxonomy_entries, metadata)
    return errors if len(errors) > 0 else None


def _validate_metadata(
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


def build_valid_taxonomy(
    taxonomy: Mapping, metadata: Optional[TaxonomyDataEntry] = None
) -> Mapping[str, TaxonomyEntry]:
    """Build valid taxonomy used to validate metadata against.

    Takes the taxonomy from the database and builds a dictionary of
    TaxonomyEntry objects, used for validation.

    :param Sequence taxonomy: From the database model
        CorpusType.valid_metadata and potentially filtered by entity key
    :param Optional[TaxonomyDataEntry] metadata: The metadata to
        validate.
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

    # TODO: Remove as part of PDCT-1435.
    if (
        all(
            k in list(taxonomy.keys())
            for k in ["allow_any", "allow_blanks", "allowed_values"]
        )
        and metadata is not None
        and metadata.keys() == [EntitySpecificTaxonomyKeys.EVENT.value]
    ):
        taxonomy_entries[EntitySpecificTaxonomyKeys.EVENT.value] = TaxonomyEntry(
            **taxonomy
        )
        return taxonomy_entries

    for key, values in taxonomy.items():
        if not isinstance(values, dict):
            raise TypeError(
                f"Taxonomy entry for '{key}' is not a dictionary: {taxonomy.keys()}, "
                f"metadata {metadata}, "
                f"{all(k in list(taxonomy.keys()) for k in ['allow_any', 'allow_blanks', 'allowed_values'])}"
                f"{all(k in ['allow_any', 'allow_blanks', 'allowed_values'] for k in list(taxonomy.keys()))}"
                f"{metadata.keys() == [EntitySpecificTaxonomyKeys.EVENT.value] if metadata is not None else None},"
                f"{list(metadata.keys()) == [EntitySpecificTaxonomyKeys.EVENT.value] if metadata is not None else None}"
            )

        # We rely on pydantic to validate the values here
        taxonomy_entries[key] = TaxonomyEntry(**values)

    return taxonomy_entries
