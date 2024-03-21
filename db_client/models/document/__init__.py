"""
The document schema.

This contains data that is shared across the navigator and the pipeline.

Notably the pipeline writes back to this part of the schema.
"""

from db_client.models.document.physical_document import PhysicalDocument

__all__ = ("PhysicalDocument",)
