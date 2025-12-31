from __future__ import annotations

import typing
from dataclasses import fields
from typing import Any

__all__ = [
    "get_dataclass_type_hints",
]


def get_dataclass_type_hints(cls, globalns: Any = None, localns: Any = None):
    types = {}
    hints = typing.get_type_hints(cls, globalns=globalns, localns=localns)
    for field in fields(cls):
        if field.name not in hints:
            continue
        types[field.name] = hints[field.name]
    return types
