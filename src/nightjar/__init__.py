"""A config dispatch library.

Use register and dispatch with plain dataclasses or Pydantic models.
"""

from nightjar.conversion import (
    Context,
    Converter,
    ConverterRegistry,
    from_dict,
    to_dict,
)
from nightjar.conversion import registry as converter_registry
from nightjar.dispatching import dispatch, register
from nightjar.registry import Field

__version__ = "0.1.0"

__all__ = [
    "Context",
    "Converter",
    "ConverterRegistry",
    "Field",
    "converter_registry",
    "dispatch",
    "from_dict",
    "register",
    "to_dict",
]
