from __future__ import annotations

import copy
import sys
from dataclasses import is_dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import (
    Any,
    ForwardRef,
    List,
    Literal,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from nightjar.utils import get_dataclass_type_hints

try:
    from types import UnionType
except ImportError:
    from typing import Union as UnionType


T = TypeVar("T")


def evaluate_forwardref(typ: ForwardRef, globalns: Any, localns: Any) -> Any:
    if sys.version_info < (3, 9):
        return typ._evaluate(globalns, localns)
    if sys.version_info < (3, 12, 4):
        return typ._evaluate(globalns, localns, set())
    # fixing error: TypeError: ForwardRef._evaluate() missing 1 required
    # keyword-only argument: 'recursive_guard'
    return from_dict(Any, typ)._evaluate(
        globalns, localns, set(), recursive_guard=set()
    )


def _to_dict_inner(obj, dict_factory, dispatch: bool = True):
    if dispatch and hasattr(obj, "_dispatch_registry"):
        return obj.__class__._dispatch_registry.dump(obj)
    elif is_dataclass(obj):
        result = []
        for fn in get_dataclass_type_hints(obj.__class__):
            value = _to_dict_inner(getattr(obj, fn), dict_factory)
            result.append((fn, value))
        return dict_factory(result)
    elif isinstance(obj, tuple):
        if hasattr(obj, "_fields"):
            return tuple(_to_dict_inner(v, dict_factory) for v in obj)
        # will return a tuple instead of named tuple
        return tuple(_to_dict_inner(v, dict_factory) for v in obj)
    elif isinstance(obj, list):
        return [_to_dict_inner(v, dict_factory) for v in obj]
    elif isinstance(obj, Mapping):
        return {
            _to_dict_inner(k, dict_factory): _to_dict_inner(v, dict_factory)
            for k, v in obj.items()
        }
    else:
        return copy.deepcopy(obj)


def to_dict(obj, dispatch: bool = True):
    return _to_dict_inner(obj, dict, dispatch=dispatch)


def from_dict(
    typ: Type[T], val: Any, globalns: Any = None, localns: Any = None
) -> T:
    if globalns is None:
        globalns = globals()
    if localns is None:
        localns = {}
    # Handle Union types
    type_args = get_args(typ)
    origin = get_origin(typ)
    if origin is not None:
        typ = origin
    # Handle Any type
    if typ is Any:
        return val
    if typ is Literal:
        if val not in type_args:
            msg = f"could not convert to literal: {typ}"
            raise ValueError(msg)
        return val
    if isinstance(typ, str):
        typ = eval(typ, globalns, localns)  # noqa: S307
    if isinstance(typ, ForwardRef):
        typ = evaluate_forwardref(typ, globalns=globalns, localns=localns)
    if typ is UnionType or typ is Union:
        for subtype in type_args:
            try:
                return from_dict(subtype, val)
            except Exception:  # noqa: S112
                continue
        msg = f"could not convert to any type in Union: {typ}"
        raise ValueError(msg)
    # check None
    if typ is None or typ is type(None):
        if val is None:
            return None
        msg = f"could not convert to None: {typ}"
        raise ValueError(msg)
    if hasattr(typ, "_dispatch_registry"):
        return typ._dispatch_registry.load(
            val, globalns=globalns, localns=localns
        )
    # Handle basic types
    if issubclass(typ, (int, float, str, bool)):
        return typ(val)
    # Handle datetime types
    if issubclass(typ, datetime):
        return datetime.fromisoformat(val)
    if issubclass(typ, date):
        return date.fromisoformat(val)
    if issubclass(typ, time):
        return time.fromisoformat(val)
    # Handle Path
    if issubclass(typ, Path):
        return Path(val)
    # Handle dataclasses
    if is_dataclass(typ):
        if isinstance(val, typ):
            return val
        if isinstance(val, Mapping):
            field_types = get_dataclass_type_hints(typ)
            kwargs = {
                k: from_dict(
                    field_types.get(k, Any),
                    v,
                    globalns=globalns,
                    localns=localns,
                )
                for k, v in val.items()
            }
            return typ(**kwargs)
        msg = f"could not convert to dataclass: {typ}, {val}"
        raise ValueError(msg)
    # Handle tuples
    if issubclass(typ, Tuple):
        try:
            if len(type_args) > 0:
                itype = Any
                if type_args[-1] is Ellipsis:
                    itype = type_args[-2]
                tuple_vals = []
                for i, item in enumerate(val):
                    tuple_vals.append(
                        from_dict(
                            type_args[i]
                            if i < len(type_args)
                            and type_args[i] is not Ellipsis
                            else itype,
                            item,
                            globalns=globalns,
                            localns=localns,
                        )
                    )
                return tuple(tuple_vals)
            return typ(
                from_dict(Any, item, globalns=globalns, localns=localns)
                for item in val
            )
        except ValueError as e:
            msg = f"could not convert to tuple: {typ}"
            raise ValueError(msg) from e
    # Handle lists
    if issubclass(typ, List):
        try:
            itype = type_args[0]
            return [
                from_dict(itype, item, globalns=globalns, localns=localns)
                for item in val
            ]
        except IndexError:
            return [
                from_dict(Any, item, globalns=globalns, localns=localns)
                for item in val
            ]
    # Handle dictionaries
    if issubclass(typ, Mapping):
        if not isinstance(val, Mapping):
            msg = f"could not convert to dict of type {typ}"
            raise ValueError(msg)
        ktype, vtype = Any, Any
        if len(type_args) == 2:
            ktype, vtype = type_args
        return {
            from_dict(ktype, k, globalns=globalns, localns=localns): from_dict(
                vtype, v, globalns=globalns, localns=localns
            )
            for k, v in dict(val).items()
        }
    msg = f"could not convert to type: {typ}"
    raise ValueError(msg)
