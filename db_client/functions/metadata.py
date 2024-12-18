import logging
from typing import Any, Mapping, Optional, Sequence, Union

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
                "event_type",  # TODO: Remove as part of PDCT-1622
                EntitySpecificTaxonomyKeys.EVENT.value,
            ]
        }
    else:
        taxonomy = get_entity_specific_taxonomy(taxonomy, entity_key)

    return validate_metadata_against_taxonomy(
        taxonomy, metadata, bool(entity_key is None)
    )


def validate_metadata_against_taxonomy(
    taxonomy: Union[TaxonomyData, TaxonomyDataEntry],
    metadata: TaxonomyDataEntry,
    is_family_metadata: bool = False,
) -> Optional[MetadataValidationErrors]:
    """Build the Corpus taxonomy for the entity & validate against it.

    :param TaxonomyDataEntry taxonomy: The Corpus taxonomy to validate against.
    :param TaxonomyDataEntry metadata: The metadata to validate.
    :param bool is_family_metadata: Whether to validate all metadata
        values as string arrays.
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

    errors = _validate_metadata(taxonomy_entries, metadata, is_family_metadata)
    return errors if len(errors) > 0 else None


def _validate_metadata(
    taxonomy_entries: Mapping[str, TaxonomyEntry],
    metadata: Mapping,
    is_family_metadata: bool = False,
) -> MetadataValidationErrors:
    """Validates the metadata against the taxonomy.

    :param _type_ taxonomy_entries: The built entries from the
        CorpusType.valid_metadata.
    :param Mapping metadata: The metadata to validate.
    :param bool is_family_metadata: Whether to validate all metadata
        values as string arrays.
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

        if not isinstance(value_list, list):
            errors.append(
                f"Invalid value '{value_list}' for metadata key '{key}' expected list."
            )
            continue

        # Ensure all items in value_list are strings
        if is_family_metadata and not all(isinstance(item, str) for item in value_list):
            errors.append(
                f"Invalid value(s) in '{value_list}' for metadata key '{key}', "
                "expected all items to be strings."
            )
            continue

        taxonomy_entry = taxonomy_entries[key]
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

    :param Mapping taxonomy: From the database model
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

    for key, values in taxonomy.items():
        _validate_taxonomy(taxonomy, key, values)

        # We rely on pydantic to validate the values here
        taxonomy_entries[key] = TaxonomyEntry(**values)

    return taxonomy_entries


def _validate_taxonomy(taxonomy: Mapping, key: str, values: Any) -> None:
    """Extra validation of the taxonomy.

    :param Mapping taxonomy: From the database model
        CorpusType.valid_metadata and potentially filtered by entity key
    :param str key: A taxonomy key.
    :param Any values: Values for a taxonomy key.
    :raises TypeError: If values is not a dictionary.
    :raises ValueError: If too many datetime_event_name values.
    :raises ValueError: If datetime_event_name value is not in list of
        allowed event_type values.
    """
    if not isinstance(values, dict):
        raise TypeError(f"Taxonomy entry for '{key}' is not a dictionary")

    if key == "datetime_event_name":
        # Compare the metadata datetime_event_name value against the list of allowed
        # event_types under _event in the taxonomy.
        datetime_event_name_values = values["allowed_values"]
        if len(datetime_event_name_values) > 1:
            raise ValueError(f"Too many values for taxonomy '{key}'")

        datetime_event_name_value = datetime_event_name_values[0]
        if datetime_event_name_value not in taxonomy["event_type"]["allowed_values"]:
            raise ValueError(
                f"Invalid value '{datetime_event_name_value}' for taxonomy '{key}'"
            )
