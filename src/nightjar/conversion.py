"""Pydantic validation with recursive conversion hooks."""

from __future__ import annotations

import copy
from dataclasses import dataclass, fields, is_dataclass, replace
from functools import lru_cache
from typing import (
    Any,
    Callable,
    ForwardRef,
    Literal,
    Mapping,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import pydantic
import pydantic.dataclasses

from nightjar.annotations import (
    evaluate_annotation,
    evaluate_forwardref,
    get_dataclass_type_hints,
)

try:
    from types import UnionType
except ImportError:
    from typing import Union as UnionType

T = TypeVar("T")


_type_adapter = getattr(pydantic, "TypeAdapter", None)
_model_types = (pydantic.BaseModel,)
_v1 = pydantic
if _type_adapter is not None:
    # Pydantic 2 can also host models created through its v1 namespace.
    from pydantic import v1 as _v1

    _model_types += (_v1.BaseModel,)


def is_model_type(typ: Any) -> bool:
    """Recognize Pydantic model classes, including v1 models in a v2 installation."""
    return (
        get_origin(typ) is None
        and isinstance(typ, type)
        and issubclass(typ, _model_types)
    )


def is_model_instance(value: Any) -> bool:
    """Return whether the value is an instance of a supported Pydantic model."""
    return isinstance(value, _model_types)


def is_validated_dataclass(typ: Any) -> bool:
    """Recognize dataclasses processed by the installed Pydantic APIs."""
    if hasattr(typ, "__pydantic_model__"):
        return True
    probe = getattr(pydantic.dataclasses, "is_pydantic_dataclass", None)
    return probe is not None and probe(typ)


@lru_cache(maxsize=128)
def _cached_adapter(typ):
    """Build and cache a Pydantic v2 TypeAdapter for a hashable type."""
    return _type_adapter(typ)


def validate(typ: Any, value: Any) -> Any:
    """Validate a value with the installed Pydantic v1 or v2 API.

    Existing model instances are returned unchanged. Legacy v1 dataclasses
    use the v1 API even within a v2 installation. Coercion, validation errors,
    and schema support follow the selected Pydantic API. Custom converter hooks
    are applied by from_dict, not this helper.
    """
    if is_model_type(typ):
        if isinstance(value, typ):
            return value
        if hasattr(typ, "model_validate"):
            return typ.model_validate(value)
        return typ.parse_obj(value)
    if hasattr(typ, "__pydantic_model__"):
        return _v1.parse_obj_as(typ, value)
    if _type_adapter is not None:
        try:
            hash(typ)
        except TypeError:
            adapter = _type_adapter(typ)
        else:
            adapter = _cached_adapter(typ)
        return adapter.validate_python(value)
    return pydantic.parse_obj_as(typ, value)


def dump_model(value: Any) -> Any:
    """Dump a Pydantic model using its native Python representation.

    Uses model_dump(mode="python") for v2 models and dict() for v1 models.
    The result is not necessarily JSON-compatible or itself a dictionary.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    return value.dict()


@dataclass(frozen=True)
class Context:
    """Immutable state shared by a conversion call.

    Carries the converter registry, annotation namespaces, current generic
    arguments.
    Use encode and decode to recurse through registered converters.
    """

    registry: ConverterRegistry
    globalns: Any = None
    localns: Any = None
    type_args: tuple = ()

    def encode(self, obj: Any) -> Any:
        """Encode a child with parent generic arguments cleared."""
        return self.registry.encode(obj, replace(self, type_args=()))

    def decode(self, typ: Any, val: Any) -> Any:
        # Child types must not inherit their parent's generic arguments.
        """Decode a child using the same namespaces but no parent generic arguments."""
        return self.registry.decode(typ, val, replace(self, type_args=()))

    def with_type_args(self, type_args: tuple) -> Context:
        """Return a context copy carrying the supplied generic arguments."""
        return replace(self, type_args=type_args)


class Converter:
    """Base class for a bidirectional to_dict/from_dict conversion rule.

    Subclasses implement only the directions they support: leave the
    ``matches_*``/``*`` pair unimplemented (they default to "no match")
    for the direction that isn't applicable.
    """

    def matches_encode(self, obj: Any, ctx: Context) -> bool:  # noqa: PLR6301 - extensible instance interface
        """Return whether this rule can encode the object; the default is False."""
        return False

    def matches_decode(self, typ: Any, ctx: Context) -> bool:  # noqa: PLR6301 - extensible instance interface
        """Return whether this rule can decode the type; the default is False."""
        return False

    def encode(self, obj: Any, ctx: Context) -> Any:
        """Encode a matched object; subclasses must implement supported directions."""
        raise NotImplementedError

    def decode(self, typ: Any, val: Any, ctx: Context) -> Any:
        """Decode a matched type; subclasses must implement supported directions."""
        raise NotImplementedError


class ConverterRegistry:
    """An ordered pipeline of :class:`Converter` objects.

    ``encode``/``decode`` walk the registered converters in order and use
    the first one that claims to handle the given object/type. Converters
    can be registered (or unregistered) at runtime to extend or override
    the to_dict/from_dict behavior for any type.
    """

    def __init__(self) -> None:
        """Create an empty registry without built-in conversion rules."""
        self._converters: list[Converter] = []

    def register(
        self, converter: Converter, *, prepend: bool = False
    ) -> Converter:
        """Insert a converter and return it.

        By default the converter is appended. Use prepend=True to give it
        priority over existing rules. The first matching rule handles a value.
        """
        if prepend:
            self._converters.insert(0, converter)
        else:
            self._converters.append(converter)
        return converter

    def unregister(self, converter: Converter) -> None:
        """Remove a converter, raising ValueError if it is not registered."""
        self._converters.remove(converter)

    def register_type(
        self,
        typ: type,
        *,
        encode: Callable[[Any], Any] | None = None,
        decode: Callable[[type, Any], Any] | None = None,
        prepend: bool = True,
    ) -> Converter:
        """Register simple encode/decode functions for a leaf type.

        ``encode`` receives the instance and returns its dict-friendly
        representation. ``decode`` receives ``(typ, val)`` and returns an
        instance of (a subclass of) ``typ``.
        """
        converter = SimpleTypeConverter(
            typ, encode_fn=encode, decode_fn=decode
        )
        return self.register(converter, prepend=prepend)

    def encode(self, obj: Any, ctx: Context) -> Any:
        """Use the first matching encoder, or deep-copy an unmatched value."""
        for converter in self._converters:
            if converter.matches_encode(obj, ctx):
                return converter.encode(obj, ctx)
        return copy.deepcopy(obj)

    def decode(self, typ: Any, val: Any, ctx: Context) -> Any:
        """Use the first matching decoder, raising ValueError if no rule matches."""
        for converter in self._converters:
            if converter.matches_decode(typ, ctx):
                return converter.decode(typ, val, ctx)
        msg = f"could not convert to type: {typ}"
        raise ValueError(msg)


class SimpleTypeConverter(Converter):
    """A leaf-type converter built from plain encode/decode functions.

    Created via :meth:`ConverterRegistry.register_type`.
    """

    def __init__(
        self,
        typ: type,
        *,
        encode_fn: Callable[[Any], Any] | None = None,
        decode_fn: Callable[[type, Any], Any] | None = None,
    ) -> None:
        """Store a leaf type and optional encoding and decoding callbacks."""
        self.type = typ
        self._encode_fn = encode_fn
        self._decode_fn = decode_fn

    def matches_encode(self, obj: Any, ctx: Context) -> bool:
        """Match instances of the configured type when an encoder is available."""
        return self._encode_fn is not None and isinstance(obj, self.type)

    def matches_decode(self, typ: Any, ctx: Context) -> bool:
        """Match subclasses of the configured type when a decoder is available."""
        return (
            self._decode_fn is not None
            and isinstance(typ, type)
            and issubclass(typ, self.type)
        )

    def encode(self, obj: Any, ctx: Context) -> Any:
        """Call the registered encoder with the object."""
        return self._encode_fn(obj)

    def decode(self, typ: Any, val: Any, ctx: Context) -> Any:
        """Call the registered decoder with the target type and input value."""
        return self._decode_fn(typ, val)


class _DefaultConverter(Converter):
    """Convert containers recursively and delegate value validation to Pydantic."""

    @staticmethod
    def matches_encode(obj: Any, ctx: Context) -> bool:
        """Recognize structured values handled by the built-in encoder."""
        return (
            is_model_instance(obj)
            or is_dataclass(obj)
            or isinstance(obj, (tuple, list, Mapping))
        )

    @staticmethod
    def matches_decode(typ: Any, ctx: Context) -> bool:
        """Recognize annotations and types handled by the built-in decoder."""
        return (
            get_origin(typ) is not None
            or isinstance(typ, (type, str, ForwardRef))
            or typ is Any
            or typ is Literal
            or typ is None
            or typ is Union
            or typ is UnionType
            or is_dataclass(typ)
        )

    @staticmethod
    def encode(obj: Any, ctx: Context) -> Any:
        """Encode structured values using registered conversion hooks."""
        if is_model_instance(obj):
            return ctx.encode(dump_model(obj))
        if is_dataclass(obj):
            return {
                field.name: ctx.encode(getattr(obj, field.name))
                for field in fields(obj)
            }
        if isinstance(obj, tuple):
            if hasattr(obj, "_fields"):
                return {
                    name: ctx.encode(getattr(obj, name))
                    for name in obj._fields
                }
            return tuple(ctx.encode(value) for value in obj)
        if isinstance(obj, list):
            return [ctx.encode(value) for value in obj]
        return {
            ctx.encode(key): ctx.encode(value) for key, value in obj.items()
        }

    @staticmethod
    def decode(typ: Any, val: Any, ctx: Context) -> Any:
        """Resolve annotations before delegating leaf validation."""
        origin = get_origin(typ)
        if origin is not None:
            return ctx.registry.decode(
                origin, val, ctx.with_type_args(get_args(typ))
            )
        if isinstance(typ, str):
            return ctx.decode(
                evaluate_annotation(typ, ctx.globalns, ctx.localns), val
            )
        if isinstance(typ, ForwardRef):
            return ctx.decode(
                evaluate_forwardref(typ, ctx.globalns, ctx.localns), val
            )
        if typ is Union or typ is UnionType:
            for subtype in ctx.type_args:
                try:
                    return ctx.decode(subtype, val)
                except Exception:  # noqa: S112 - try remaining union alternatives
                    continue
            msg = f"could not convert to any type in Union: {typ}"
            raise ValueError(msg)
        if is_model_type(typ):
            return validate(typ, val)
        if is_dataclass(typ):
            return _decode_dataclass(typ, val, ctx)
        if isinstance(typ, type):
            if issubclass(typ, tuple):
                return _decode_tuple(typ, val, ctx)
            if issubclass(typ, list):
                item_type = ctx.type_args[0] if ctx.type_args else Any
                return [ctx.decode(item_type, item) for item in val]
            if issubclass(typ, Mapping):
                if not isinstance(val, Mapping):
                    msg = f"could not convert to dict of type {typ}"
                    raise ValueError(msg)
                key_type, value_type = (
                    ctx.type_args if len(ctx.type_args) == 2 else (Any, Any)
                )
                return {
                    ctx.decode(key_type, key): ctx.decode(value_type, value)
                    for key, value in dict(val).items()
                }
        if typ is None:
            typ = type(None)
        if ctx.type_args:
            typ = typ[ctx.type_args]
        return validate(typ, val)


def _decode_dataclass(typ, val, ctx):
    """Build a dataclass from input data or preserve an existing instance.

    Pydantic dataclasses run their native validation. Plain dataclasses convert
    declared fields recursively and reject unknown keys.
    """
    if isinstance(val, typ):
        return val
    if is_validated_dataclass(typ):
        return validate(typ, val)
    if not isinstance(val, Mapping):
        msg = f"could not convert to dataclass: {typ}, {val}"
        raise ValueError(msg)
    hints = get_dataclass_type_hints(typ)
    unknown = val.keys() - hints.keys()
    if unknown:
        names = ", ".join(sorted(map(str, unknown)))
        msg = f"Undeclared fields for {typ.__name__} include {names}"
        raise TypeError(msg)
    return typ(**{
        key: ctx.decode(hints[key], value) for key, value in val.items()
    })


def _decode_tuple(typ, val, ctx):
    """Convert tuple elements using positional or variadic type arguments.

    Extra elements in fixed-length annotations fall back to Any; this helper
    does not enforce the annotated tuple length.
    """
    args = ctx.type_args
    try:
        if not args:
            return typ(ctx.decode(Any, item) for item in val)
        fallback = args[-2] if args[-1] is Ellipsis else Any
        return tuple(
            ctx.decode(
                args[index]
                if index < len(args) and args[index] is not Ellipsis
                else fallback,
                item,
            )
            for index, item in enumerate(val)
        )
    except ValueError as exc:
        msg = f"could not convert to tuple: {typ}"
        raise ValueError(msg) from exc


registry = ConverterRegistry()
registry.register(_DefaultConverter())


def to_dict(obj: Any) -> Any:
    """Convert an object to a nested Python representation.

    Parameters
    ----------
    obj : object
        Value to encode through the shared converter registry.

    Returns
    -------
    object
        Encoded value. Dataclasses and named tuples become dictionaries;
        ordinary tuples remain tuples. Unmatched values are deep-copied.

    Notes
    -----
    The result is not guaranteed to be a dictionary or JSON-compatible.
    Custom encoders and native Pydantic model serialization may return other
    Python values.
    """
    ctx = Context(registry=registry)
    return registry.encode(obj, ctx)


def from_dict(
    typ: Type[T], val: Any, globalns: Any = None, localns: Any = None
) -> T:
    """Convert a Python value into the requested type.

    Parameters
    ----------
    typ : type or typing annotation
        Target type, generic alias, string annotation, or forward reference.
    val : object
        Input value, commonly a dictionary or nested container.
    globalns, localns : dict, optional
        Namespaces forwarded to string and forward-reference conversion.
        Plain dataclass field hints use their defining-module namespaces.

    Returns
    -------
    object
        The converted value.

    Notes
    -----
    Custom converters take priority according to registry order. Nightjar
    handles recursive containers; Pydantic validates remaining
    values. Ordinary unions try alternatives in order and return the first
    successful conversion. Pydantic coercion depends on its installed version.
    Conversion errors propagate unless a later union alternative succeeds.
    """
    if globalns is None:
        globalns = globals()
    if localns is None:
        localns = {}
    ctx = Context(registry=registry, globalns=globalns, localns=localns)
    return registry.decode(typ, val, ctx)
