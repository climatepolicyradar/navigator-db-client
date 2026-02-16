import logging
from typing import Mapping, Optional, Sequence, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_client.models.organisation import Corpus, CorpusType

_LOGGER = logging.getLogger(__name__)

TaxonomyDataEntry = Mapping[str, Union[bool, str, Sequence[str]]]
TaxonomyData = Mapping[
    str, Mapping[str, Union[TaxonomyDataEntry, bool, str, Sequence[str]]]
]


def get_taxonomy_from_corpus(db: Session, corpus_id: str) -> Optional[TaxonomyData]:
    """Get the taxonomy of a corpus.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to get the
        taxonomy for.
    :return Optional[TaxonomyData]: The taxonomy of the given corpus or
        None.
    """
    stmt = (
        select(CorpusType.valid_metadata)
        .join(Corpus, Corpus.corpus_type_name == CorpusType.name)
        .where(Corpus.import_id == corpus_id)
        .distinct()
    )
    return db.execute(stmt).scalar_one_or_none()


def get_taxonomy_by_corpus_type_name(db: Session, corpus_type_name: str):
    """Get the taxonomy of a corpus by type name.
    :param Session db: The DB session to connect to.
    :param str corpus_type_name: The name of the corpus type we want to get the
        taxonomy for.
    :return Optional[TaxonomyData]: The taxonomy of the given corpus or
        None.
    """
    stmt = select(CorpusType.valid_metadata).where(CorpusType.name == corpus_type_name)
    return db.execute(stmt).scalar_one_or_none()


def get_entity_specific_taxonomy(
    taxonomy, _entity_key: Optional[str] = None
) -> TaxonomyDataEntry:
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
