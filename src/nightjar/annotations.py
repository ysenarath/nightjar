"""Annotation inspection and resolution, including Python 3.9 unions."""

from __future__ import annotations

import ast
import functools
import inspect
import operator
import sys
import types
import typing
from dataclasses import fields
from typing import Annotated, Any, ForwardRef, get_origin
from uuid import uuid4

from typing_extensions import evaluate_forward_ref
from typing_extensions import get_annotations as _get_annotations

__all__ = [
    "evaluate_forwardref",
    "get_annotations",
    "get_dataclass_type_hints",
]


class ONLY_IF_ALL_STR_type:  # noqa: N801
    """Sentinel type selecting evaluation only when every annotation is a string."""
    def __repr__(self):
        """Return the display name of the string-evaluation sentinel."""
        return "<ONLY_IF_ALL_STR>"


ONLY_IF_ALL_STR = ONLY_IF_ALL_STR_type()
NoneType = type(None)


def get_annotations(
    obj, globals=None, locals=None, *, eval_str=ONLY_IF_ALL_STR
):
    """Return annotations with optional evaluation of string values.

    Parameters
    ----------
    obj : object
        A class, module, or callable accepted by typing_extensions.
        Inherited class annotations are excluded.
    globals, locals : dict, optional
        Namespaces used to evaluate strings. Globals default to the module,
        the class's defining module, or the unwrapped callable's globals.
        When locals are omitted, evaluation uses the global namespace.
    eval_str : bool or ONLY_IF_ALL_STR, optional
        True evaluates string values; False preserves them. The default
        evaluates strings only when all annotation values are strings.

    Returns
    -------
    dict
        Annotation names mapped to their original or evaluated values.

    Notes
    -----
    Python 3.9 union expressions are supported during evaluation. Non-string
    values are preserved, and a quoted string is evaluated only once.
    Retrieval and evaluation errors propagate to the caller.
    """
    ann = _get_annotations(obj, eval_str=False)
    # Preserve the existing callable dictionary identity when not evaluating.
    if callable(obj) and not isinstance(obj, type):
        original = getattr(obj, "__annotations__", None)
        if original is not None:
            ann = original
    if not ann:
        return ann
    if eval_str is ONLY_IF_ALL_STR:
        eval_str = all(isinstance(value, str) for value in ann.values())
    if not eval_str:
        return ann

    if globals is None:
        if isinstance(obj, types.ModuleType):
            globals = vars(obj)
        else:
            globals = (
                vars(sys.modules[obj.__module__])
                if isinstance(obj, type)
                else {}
            )
            unwrapped = inspect.unwrap(obj)
            while isinstance(unwrapped, functools.partial):
                unwrapped = inspect.unwrap(unwrapped.func)
            globals = getattr(unwrapped, "__globals__", globals)
    return {
        key: evaluate_annotation(value, globals, locals)
        if isinstance(value, str)
        else value
        for key, value in ann.items()
    }


def get_dataclass_type_hints(cls, globalns: Any = None, localns: Any = None):
    """Resolve annotations for actual dataclass fields, including inherited fields.

    ClassVar and InitVar annotations are excluded from the result. Explicit
    namespaces are used for resolution; otherwise defining-module namespaces
    are used. Python 3.9 resolution supports postponed union expressions.
    Annotated metadata is stripped, as with typing.get_type_hints.
    """
    if sys.version_info < (3, 10):
        hints = get_class_type_hints_39(cls, globalns, localns)
    else:
        hints = typing.get_type_hints(cls, globalns=globalns, localns=localns)
    return {
        field.name: hints[field.name]
        for field in fields(cls)
        if field.name in hints
    }


def evaluate_forwardref(typ: ForwardRef, globalns: Any, localns: Any) -> Any:
    """Resolve a ForwardRef using the supplied global and local namespaces.

    Uses Nightjar's union backport on Python 3.9 and typing_extensions on
    newer Python versions. Unresolved names raise NameError.
    """
    if sys.version_info < (3, 10):
        return resolve_type_39(typ, globalns, localns)
    return evaluate_forward_ref(
        typ, globals=globalns, locals=localns, type_params=()
    )


def is_annotated(type_hint):
    """Return whether the type hint is an Annotated alias."""
    return get_origin(type_hint) is Annotated


def _union(left, right):
    """Apply the native OR operator, falling back to typing.Union for types."""
    try:
        return operator.or_(left, right)
    except TypeError as exc:
        if not str(exc).startswith("unsupported operand type(s) for |:"):
            raise
        return typing.Union[left, right]


class _UnionTransformer(ast.NodeTransformer):
    """Rewrite OR expressions to calls to a named compatibility helper."""
    def __init__(self, helper_name):
        """Store the name under which the evaluation helper will be available."""
        self.helper_name = helper_name

    def visit_BinOp(self, node):
        """Rewrite bitwise OR nodes while preserving other binary operations."""
        node = self.generic_visit(node)
        if isinstance(node.op, ast.BitOr):
            return ast.copy_location(
                ast.Call(
                    func=ast.Name(id=self.helper_name, ctx=ast.Load()),
                    args=[node.left, node.right],
                    keywords=[],
                ),
                node,
            )
        return node


def evaluate_annotation(expression, globalns, localns):
    """Evaluate one annotation expression in the supplied namespaces.

    Python 3.9 OR expressions use a compatibility helper in copied namespaces.
    Other expressions use eval directly. String results remain strings;
    recursive forward-reference resolution is handled separately.
    """
    if sys.version_info >= (3, 10):
        return eval(expression, globalns, localns)  # noqa: S307

    tree = ast.parse(expression, mode="eval")
    if not any(isinstance(node, ast.BitOr) for node in ast.walk(tree)):
        return eval(expression, globalns, localns)  # noqa: S307

    # A fresh name prevents collisions with names in the user's annotation.
    # Inject into copies so annotation resolution doesn't modify namespaces.
    helper_name = f"_nightjar_union_{uuid4().hex}"
    tree = ast.fix_missing_locations(
        _UnionTransformer(helper_name).visit(tree)
    )
    eval_globals = dict(globalns)
    eval_globals[helper_name] = _union
    eval_locals = dict(localns) if localns is not None else eval_globals
    eval_locals[helper_name] = _union
    return eval(  # noqa: S307
        compile(tree, "<annotation>", "eval"), eval_globals, eval_locals
    )


def resolve_type_39(
    value, globalns=None, localns=None, recursive_guard=frozenset()
):
    """Resolve forward references and generic arguments on Python 3.9.

    Literal values and Annotated metadata are preserved. A recursion guard
    leaves references unresolved when revisiting the same expression, so
    recursive aliases terminate. This helper uses Python 3.9 typing internals.
    """
    if globalns is None:
        globalns = localns if localns is not None else {}
    if localns is None:
        localns = globalns
    if isinstance(value, str):
        value = typing.ForwardRef(value)
    if isinstance(value, typing.ForwardRef):
        expression = value.__forward_arg__
        if expression in recursive_guard:
            return value
        module = getattr(value, "__forward_module__", None)
        if module is not None:
            globalns = getattr(sys.modules.get(module), "__dict__", globalns)
        resolved = evaluate_annotation(expression, globalns, localns)
        resolved = typing._type_check(
            resolved,
            "Forward references must evaluate to types.",
            is_argument=value.__forward_is_argument__,
            allow_special_forms=getattr(value, "__forward_is_class__", False),
        )
        return resolve_type_39(
            resolved, globalns, localns, recursive_guard | {expression}
        )
    if isinstance(value, (types.GenericAlias, typing._GenericAlias)):
        if typing.get_origin(value) is typing.Literal:
            return value
        args = tuple(
            resolve_type_39(arg, globalns, localns, recursive_guard)
            for arg in value.__args__
        )
        if args == value.__args__:
            return value
        if isinstance(value, types.GenericAlias):
            return types.GenericAlias(value.__origin__, args)
        return value.copy_with(args)
    return value


def get_class_type_hints_39(cls, globalns=None, localns=None):
    """Collect resolved class annotations across the MRO on Python 3.9.

    Subclass annotations override inherited names. Each base uses its defining
    module unless globalns is supplied. Annotated metadata is removed, and
    classes marked with no_type_check return an empty dictionary.
    """
    if getattr(cls, "__no_type_check__", None):
        return {}
    hints = {}
    for base in reversed(cls.__mro__):
        base_globals = (
            sys.modules[base.__module__].__dict__
            if globalns is None
            else globalns
        )
        # Python 3.9 stores class annotations directly in the class dictionary.
        annotations = base.__dict__.get("__annotations__", {})  # noqa: RUF063
        for name, value in annotations.items():
            if value is None:
                value = type(None)
            if isinstance(value, str):
                value = typing.ForwardRef(
                    value, is_argument=False, is_class=True
                )
            hints[name] = typing._strip_annotations(
                resolve_type_39(value, base_globals, localns)
            )
    return hints
