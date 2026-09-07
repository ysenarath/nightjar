"""Register constructors and dispatch configuration without base classes.

Examples
--------
>>> from dataclasses import dataclass
>>> @dataclass
... class Settings:
...     count: int = 1
>>> @register(Settings, kind="worker")
... @dataclass
... class Worker:
...     config: Settings
>>> dispatch(Settings, {"kind": "worker", "count": "2"}).config.count
2
"""

from __future__ import annotations

import inspect
import sys
from collections.abc import Callable, Mapping
from typing import Annotated, Any, ForwardRef, TypeVar, get_args, get_origin

from nightjar.annotations import evaluate_forwardref, get_annotations
from nightjar.conversion import from_dict
from nightjar.registry import Expression, Field

T = TypeVar("T")
_MISSING = object()
_rules: dict[tuple[type, Callable], tuple[Expression, ...]] = {}


def _get_constructor(config: Any) -> Callable:
    """Return the unique constructor registered for a class or instance.

    Raises ValueError for missing or ambiguous registrations. Instance dispatch
    uses the exact configuration type, without re-evaluating input predicates.
    """
    typ = config if isinstance(config, type) else type(config)
    candidates = [ctor for config_type, ctor in _rules if config_type is typ]
    if len(candidates) != 1:
        names = ", ".join(
            sorted(
                getattr(c, "__name__", type(c).__name__) for c in candidates
            )
        )
        msg = f"Expected one implementation for {typ.__name__}, found {len(candidates)}"
        if names:
            msg += f" ({names})"
        raise ValueError(msg)
    return next(iter(candidates))


def _infer_config(constructor: Callable) -> type:
    """Resolve the config annotation, requiring one concrete configuration type."""
    owner = constructor
    if isinstance(constructor, type):
        owner = next(
            (
                base
                for base in constructor.__mro__
                if "config" in get_annotations(base, eval_str=False)
            ),
            constructor,
        )
    else:
        owner = inspect.unwrap(constructor)
        parameters = list(inspect.signature(owner).parameters.values())
        if (
            not parameters
            or parameters[0].name != "config"
            or parameters[0].kind
            not in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            }
        ):
            msg = "Inferred constructors must accept config as their first positional parameter"
            raise TypeError(msg)
    annotation = get_annotations(owner, eval_str=False).get("config", _MISSING)
    namespace = getattr(
        owner, "__globals__", vars(sys.modules[owner.__module__])
    )
    try:
        if isinstance(annotation, str):
            annotation = ForwardRef(annotation)
        if isinstance(annotation, ForwardRef):
            annotation = evaluate_forwardref(annotation, namespace, namespace)
    except (NameError, TypeError, SyntaxError) as exc:
        msg = "Cannot resolve the config annotation at registration time; pass its type explicitly"
        raise TypeError(msg) from exc
    if get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]
    if not isinstance(annotation, type) or annotation is Any:
        msg = "Registration requires one concrete config annotation or an explicit configuration type"
        raise TypeError(msg)
    return annotation


def register(*args: Expression | type, **kwargs: Any) -> Callable[[T], T]:
    """Register a constructor with expressions and field equality matches.

    Parameters
    ----------
    *args : Expression or type
        Predicates evaluated against raw input before conversion. An optional
        first configuration type overrides annotation inference. Otherwise,
        infer from a class's config attribute or a function's first config
        parameter. Use @register() when no matching conditions are needed.
    **kwargs : object
        Required top-level field values. Each becomes a presence check and
        equality expression. Missing keys never match, even for None values.
        Every keyword is a field name, including when and config.

    Returns
    -------
    Callable
        Decorator preserving the constructor, which receives one converted
        configuration argument. Re-registration replaces the rules for the
        same constructor and configuration type.

    Notes
    -----
    All conditions must match. Dispatch loops through registrations and
    requires exactly one match. Stack decorators to register multiple config
    types. Class-level __match__ attributes are not used.
    """
    config = args[0] if args and isinstance(args[0], type) else None
    if config is not None:
        args = args[1:]
    if any(not isinstance(arg, Expression) for arg in args):
        msg = "Positional matching arguments must be Expressions"
        raise TypeError(msg)
    expressions = args + tuple(
        Field(key).exists() & (Field(key) == value)
        for key, value in kwargs.items()
    )

    def decorator(constructor: T) -> T:
        """Store the constructor and its expressions without wrapping it."""
        if not callable(constructor):
            msg = "The registered implementation must be callable"
            raise TypeError(msg)
        config_type = (
            config if config is not None else _infer_config(constructor)
        )
        _rules[config_type, constructor] = expressions
        return constructor

    return decorator


def dispatch(cls: Any, config: Any = _MISSING) -> Any:
    """Convert configuration and call its uniquely selected constructor.

    Parameters
    ----------
    cls : type or object
        Configuration class or family when data is supplied. With one argument,
        an existing configuration instance whose exact type is registered.
    config : object, optional
        Input mapping or instance of cls. Mapping rules are checked before
        conversion; exactly one constructor must match.

    Returns
    -------
    object
        Result of calling the registered constructor with the configuration.

    Raises
    ------
    ValueError
        No registration or multiple registrations match.
    TypeError
        The two-argument form is not given a class and mapping or instance.

    Notes
    -----
    Validation and constructor exceptions propagate.
    """
    if config is _MISSING:
        if isinstance(cls, type):
            msg = "Supply configuration data when dispatching a class"
            raise TypeError(msg)
        return _get_constructor(cls)(cls)
    if not isinstance(cls, type):
        msg = "The first argument must be a configuration class"
        raise TypeError(msg)
    if isinstance(config, cls):
        return _get_constructor(config)(config)
    if not isinstance(config, Mapping):
        msg = "Configuration data must be a mapping or configuration instance"
        raise TypeError(msg)
    candidates = []
    for (typ, constructor), expressions in _rules.items():
        if not issubclass(typ, cls):
            continue
        if not all(expression.evaluate(config) for expression in expressions):
            continue
        candidates.append((typ, constructor))
    if len(candidates) != 1:
        names = ", ".join(
            sorted(
                f"{typ.__name__} -> {getattr(ctor, '__name__', type(ctor).__name__)}"
                for typ, ctor in candidates
            )
        )
        msg = f"Expected one registration for {cls.__name__}, found {len(candidates)}"
        if names:
            msg += f" ({names})"
        raise ValueError(msg)
    typ, constructor = candidates[0]
    return constructor(from_dict(typ, config))
