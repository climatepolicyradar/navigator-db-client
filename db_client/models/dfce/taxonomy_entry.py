"""
Taxonomy Entry is a representation of a single taxonomy field. It is used to validate metadata values against a taxonomy.

The fields define how metadata gets validated:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
| allow_any | allow_blanks  | Behaviour
-----------------------------------------------------------------------------
| True      | True          | allowed_values is ignored and anything goes
-----------------------------------------------------------------------------
| True      | False         | allowed_values is ignored but you need a
|           |               | non-blank value
-----------------------------------------------------------------------------
| False     | True          | allowed_values is used to validate, blank is
|           |               | also valid
-----------------------------------------------------------------------------
| False     | False         | allowed_values is used to validate, blank is
|           |               | invalid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from enum import Enum
from typing import Mapping, Sequence

from pydantic.config import ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass


class EntitySpecificTaxonomyKeys(str, Enum):
    """Entities that are to be counted."""

    Document = "_document"


@pydantic_dataclass(config=ConfigDict(validate_assignment=True, extra="forbid"))
class TaxonomyEntry:
    """Details a single taxonomy field"""

    allow_blanks: bool
    allowed_values: Sequence[str]
    allow_any: bool = False


Taxonomy = Mapping[str, TaxonomyEntry]
