from __future__ import annotations

import functools
import sys
import types
import typing
from dataclasses import fields
from typing import Annotated, Any, get_origin

__all__ = [
    "get_annotations",
    "get_dataclass_type_hints",
]


class ONLY_IF_ALL_STR_type:  # noqa: N801
    def __repr__(self):
        return "<ONLY_IF_ALL_STR>"


ONLY_IF_ALL_STR = ONLY_IF_ALL_STR_type()
NoneType = type(None)


def get_annotations(
    obj, globals=None, locals=None, *, eval_str=ONLY_IF_ALL_STR
):
    """Compute the annotations dict for an object.

    obj may be a callable, class, or module.
    Passing in any other type of object raises TypeError.

    This function handles several details for you:

      * Values of type str may be un-stringized using eval(),
        depending on the value of eval_str.  This is intended
        for use with stringized annotations
        (from __future__ import annotations).
      * If obj doesn't have an annotations dict, returns an
        empty dict.  (Functions and methods always have an
        annotations dict; classes, modules, and other types of
        callables may not.)
      * Ignores inherited annotations on classes.  If a class
        doesn't have its own annotations dict, returns an empty dict.
      * Always, always, always returns a dict.

    eval_str controls whether or not values of type str are replaced
    with the result of calling eval() on those values:
      * If eval_str is true, eval() is called on values of type str.
      * If eval_str is false, values of type str are unchanged.
      * If eval_str is the special value inspect.ONLY_IF_ALL_STR,
        which is the default, eval() is called on values of type str
        only if *every* value in the dict is of type str.  This is a
        heuristic; the goal is to only eval() stringized annotations.
        (If, in a future version of Python, get_annotations() is able
        to determine authoritatively whether or not an annotations
        dict contains stringized annotations, inspect.ONLY_IF_ALL_STR
        will use that authoritative source instead of the heuristic.)

    globals and locals are passed in to eval(); see the documentation
    for eval() for more information.  If globals is None,
    get_annotations() uses a context-specific default value,
    contingent on type(obj):
      * If obj is a module, globals defaults to obj.__dict__.
      * If obj is a class, globals defaults to
        sys.modules[obj.__module__].__dict__.
      * If obj is a callable, globals defaults to obj.__globals__,
        although if obj is a wrapped function (using
        functools.update_wrapper()) it is first unwrapped.

    """
    if isinstance(obj, (type, types.ModuleType)):
        ann = obj.__dict__.get("__annotations__", {})
        if isinstance(obj, type):
            # class
            obj_globals = sys.modules[obj.__module__].__dict__
            unwrap = obj
        else:
            # module
            obj_globals = obj.__dict__
            unwrap = None
    elif callable(obj):
        # this includes types.Function, types.BuiltinFunctionType,
        # types.BuiltinMethodType, functools.partial, functools.singledispatch,
        # etc etc etc...
        ann = getattr(obj, "__annotations__", {})
        obj_globals = obj.__globals__
        unwrap = obj
    else:
        msg = f"{obj!r} is not a module, class, or callable."
        raise TypeError(msg)

    if ann is None:
        return {}

    if not isinstance(ann, dict):
        msg = f"{obj!r}.__annotations__ is neither a dict nor None"
        raise ValueError(msg)

    if not ann:
        return ann

    if eval_str is ONLY_IF_ALL_STR:
        eval_str = all(isinstance(v, str) for v in ann.values())
    if not eval_str:
        return ann

    if unwrap is not None:
        while True:
            if hasattr(unwrap, "__wrapped__"):
                unwrap = unwrap.__wrapped__
                continue
            if isinstance(unwrap, functools.partial):
                unwrap = unwrap.func
                continue
            break
        if hasattr(unwrap, "__globals__"):
            obj_globals = unwrap.__globals__

    if globals is None:
        globals = obj_globals

    return_value = {
        key: value
        if not isinstance(value, str)
        else eval(value, globals, locals)  # noqa: S307
        for key, value in ann.items()
    }
    return return_value


def get_dataclass_type_hints(cls, globalns: Any = None, localns: Any = None):
    types = {}
    hints = typing.get_type_hints(cls, globalns=globalns, localns=localns)
    for field in fields(cls):
        if field.name not in hints:
            continue
        types[field.name] = hints[field.name]
    return types


def is_annotated(type_hint):
    return get_origin(type_hint) is Annotated
