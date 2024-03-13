""" Export pre-population functions for all fixed metadata tables """

from db_client.data_migrations.populate_counters import populate_counters
from db_client.data_migrations.populate_document_role import populate_document_role
from db_client.data_migrations.populate_document_type import populate_document_type
from db_client.data_migrations.populate_document_variant import (
    populate_document_variant,
)
from db_client.data_migrations.populate_event_type import populate_event_type
from db_client.data_migrations.populate_geo_statistics import populate_geo_statistics
from db_client.data_migrations.populate_geography import populate_geography
from db_client.data_migrations.populate_language import populate_language
from db_client.data_migrations.populate_taxonomy import populate_taxonomy

__all__ = (
    "populate_counters",
    "populate_document_role",
    "populate_document_type",
    "populate_document_type",
    "populate_document_variant",
    "populate_event_type",
    "populate_geo_statistics",
    "populate_geography",
    "populate_language",
    "populate_taxonomy",
)
