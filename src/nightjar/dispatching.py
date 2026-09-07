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

from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from nightjar.conversion import from_dict
from nightjar.registry import Expression

T = TypeVar("T")
_MISSING = object()
_rules: dict[tuple[type, Callable], tuple[Expression | None, dict]] = {}


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


def register(
    *config: type, when: Expression | None = None, **match: Any
) -> Callable[[T], T]:
    """Register a constructor for one or more configuration types.

    Parameters
    ----------
    *config : type
        Plain dataclass or Pydantic model types.
    when : Expression, optional
        Additional predicate evaluated against the input mapping.
    **match : object
        Required top-level discriminator values, for example kind="worker".
        Missing keys never match, even when the required value is None.

    Returns
    -------
    Callable
        Decorator preserving the constructor, which receives one converted
        configuration argument. Re-registering the same constructor and type
        replaces their selection rule.

    Notes
    -----
    A configuration family's registered subclasses participate in dispatch.
    No Nightjar base class or metaclass is required. Without explicit rules,
    a type's __match__ predicate is used when present.
    """
    if not config or any(not isinstance(typ, type) for typ in config):
        msg = "Registration requires at least one configuration class"
        raise TypeError(msg)
    if when is not None and not isinstance(when, Expression):
        msg = "when must be a Field expression"
        raise TypeError(msg)

    def decorator(constructor: T) -> T:
        """Store the constructor and its rules without wrapping it."""
        if not callable(constructor):
            msg = "The registered implementation must be callable"
            raise TypeError(msg)
        for typ in config:
            _rules[typ, constructor] = (when, dict(match))
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
    for (typ, constructor), (predicate, match) in _rules.items():
        if not issubclass(typ, cls):
            continue
        if not all(
            key in config and config[key] == val for key, val in match.items()
        ):
            continue
        if predicate is None:
            predicate = getattr(typ, "__match__", None)
        if predicate is not None and not predicate.evaluate(config):
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
