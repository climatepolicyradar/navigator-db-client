"""
Schema for counters.

The following section includes the necessary schema for maintaining the counts
of different entity types. These are scoped per "data source" - however the
concept of "data source" is not yet implemented, see PDCT-431.
"""

import logging
from enum import Enum
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql import text

from db_client.models.base import Base
from db_client.models.organisation.organisation import Organisation

_LOGGER = logging.getLogger(__name__)

#
# DO NOT ADD TO THIS LIST BELOW
#
# NOTE: These need to change when we introduce "Data source" (PDCT-431)
ORGANISATION_CCLW = "CCLW"
ORGANISATION_UNFCCC = "UNFCCC"


class CountedEntity(str, Enum):
    """Entities that are to be counted."""

    Collection = "collection"
    Family = "family"
    Document = "document"
    Event = "event"
    Corpus = "corpus"


class EntityCounter(Base):
    """
    A list of entity counters per organisation name.

    NOTE: There is no foreign key, as this is expected to change
    when we introduce data sources (PDCT-431). So at this time a
    FK to the new datasource table should be introduced.

    This is used for generating import_ids in the following format:

        <organisation.name>.<entity>.<counter>.<n>

    """

    __tablename__ = "entity_counter"

    _get_and_increment = text(
        """
        WITH updated AS (
        UPDATE entity_counter SET counter = COALESCE(counter, 0) + 1
        WHERE id = :id RETURNING counter
        )
        SELECT counter FROM updated;
        """
    )

    id = sa.Column(sa.Integer, primary_key=True)
    description = sa.Column(sa.String, nullable=False, default="")
    prefix = sa.Column(sa.ForeignKey(Organisation.name), nullable=False)
    counter = sa.Column(sa.Integer, nullable=False, server_default="0")

    def get_next_count(self) -> str:
        """
        Gets the next counter value and updates the row.

        :return str: The next counter value.
        """
        try:
            db: Optional[Session] = object_session(self)

            if db is None:
                _LOGGER.exception("When creating object session")
                raise

            cmd = self._get_and_increment.bindparams(id=self.id)
            value = cast(str, db.execute(cmd).scalar())
            db.commit()
            return value
        except:
            _LOGGER.exception(f"When generating counter for {self.prefix}")
            raise

    def create_import_id(self, entity: CountedEntity) -> str:
        """
        Creates a unique import id.

        This uses the n-value of zero to conform to existing format.

        :param CountedEntity entity: The entity you want counted
        :raises RuntimeError: raised when the prefix is not an organisation.
        :return str: The fully formatted import_id
        """

        # Validation - this prefix used to be validated as the Organisation name
        # this has been removed as we expect many organisations. Should we query
        # for the organisation to continue validation?

        n = 0  # The fourth quad is historical
        i_value = str(self.get_next_count()).zfill(8)
        n_value = str(n).zfill(4)
        return f"{self.prefix}.{entity.value}.i{i_value}.n{n_value}"
