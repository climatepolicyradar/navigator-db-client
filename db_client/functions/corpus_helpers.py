import logging
from typing import Mapping, Optional, Sequence, Union

from sqlalchemy.orm import Session

from db_client.models.organisation import Corpus, CorpusType

_LOGGER = logging.getLogger(__name__)

TaxonomyData = Mapping[str, Mapping[str, Union[dict, bool, str, Sequence[str]]]]


def get_taxonomy_from_corpus(db: Session, corpus_id: str) -> Optional[TaxonomyData]:
    """Get the taxonomy of a corpus.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to get the
        taxonomy for.
    :return Optional[TaxonomyData]: The taxonomy of the given corpus or
        None.
    """
    return (
        db.query(CorpusType.valid_metadata)
        .join(Corpus, Corpus.corpus_type_name == CorpusType.name)
        .filter(Corpus.import_id == corpus_id)
        .scalar()
    )


def get_entity_specific_taxonomy(
    taxonomy, _entity_key: Optional[str] = None
) -> Optional[TaxonomyData]:
    """Validates the Family's metadata against its Corpus' Taxonomy.

    :param dict taxonomy: The Corpus taxonomy to validate against.
    :param str _entity_key: The family metadata to validate.
    :raises TypeError: If the entity specific taxonomy key isn't present.
    :return dict: The entity specific taxonomy if found or the passed
        taxonomy.
    """
    if taxonomy is not None and _entity_key is not None:
        if _entity_key not in taxonomy.keys():
            raise TypeError(f"Cannot find {_entity_key} taxonomy data in database")
        taxonomy = taxonomy[_entity_key]
    return taxonomy
