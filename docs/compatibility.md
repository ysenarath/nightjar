# Compatibility

## Python 3.9 and later

Nightjar supports Python 3.9+. On Python 3.9, postpone annotation evaluation to
use `A | B` in annotations that Nightjar resolves:

```python
from __future__ import annotations

from dataclasses import dataclass
from nightjar import from_dict


@dataclass
class Options:
    retries: int | None = None


assert from_dict(Options, {"retries": "3"}).retries == 3
```

The future import affects annotations only. A runtime alias such as
`Alias = int | str` still requires Python 3.10+. Use `typing.Union[int, str]`
for runtime aliases on Python 3.9. Pydantic models use Pydantic's own annotation
handling; Nightjar's resolver does not change what that version accepts.

## Pydantic versions

Nightjar supports Pydantic v1.10 and v2 without an exact dependency pin. It uses
the installed version's APIs. Installing Nightjar through uv resolves a
compatible Pydantic release if necessary; Nightjar does not install dependencies
at runtime. Support for future major versions is not implied.

Validation, coercion, and model serialization follow the installed version.
Applications that need identical validation behavior across environments should
manage their Pydantic version in their own dependency constraints and lockfile.

## Imports

Import `from_dict`, `to_dict`, and `converter_registry` from `nightjar`.
The former `nightjar.serializers` and `nightjar.utils` modules have been removed.
Annotation helpers live in `nightjar.annotations`; most applications can use the
top-level conversion API without calling them directly.

## Migrating from the inheritance API

`BaseConfig`, `BaseModule`, `AutoModule`, and `DispatchRegistry` have been removed.

- Replace configuration subclasses of `BaseConfig` with plain `@dataclass`
  classes or Pydantic models. Decorate each plain dataclass subclass explicitly.
- Replace implementation subclasses of `BaseModule` with plain classes that
  accept a configuration. Annotate `config` and use `@register(kind="value")`,
  or pass the config type explicitly.
- Replace `AutoModule(config)` with `dispatch(config)`.
- Replace family-level `Config.from_dict(data)` followed by construction with
  `dispatch(Config, data)`. For conversion alone, use `from_dict(ConcreteConfig, data)`.
- Replace class-level `dispatch=["kind"]` with keyword matches on `@register`.
  Pass predicates as positional expressions. The old `when=`
  parameter and class-level `__match__` convention no longer define predicates;
  `when=` now matches an input field named `when`.
- Remove the `dispatch` argument from `to_dict`. Registration discriminators are
  no longer injected into output; use declared fields when they should persist.

Plain classes do not inherit the old mapping interface or automatic initialization
hooks. Use attributes to read configuration and initialize implementations in
`__init__`, or use a dataclass with its standard `__post_init__` hook.
