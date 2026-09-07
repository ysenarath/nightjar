# For AI agents

Use this guide when generating code that uses Nightjar. It describes the current
registration API; older examples using Nightjar base classes are incompatible.
A compact documentation index is available at [llms.txt](llms.txt).

## Install and import

```bash
uv add nightjar
```

Import `dispatch`, `register`, `Field`, `from_dict`, and `to_dict` from `nightjar`
as needed. Nightjar supports Python 3.9+ and Pydantic v1.10/v2. Use the installed
Pydantic version's APIs; Nightjar does not install dependencies at runtime.

## Preferred pattern

Use a shared config family when input selects between implementations. Infer the
concrete config type from each implementation's `config` annotation:

```python
from dataclasses import dataclass
from nightjar import dispatch, register, to_dict


@dataclass
class StorageConfig:
    pass


@dataclass
class LocalConfig(StorageConfig):
    kind: str = "local"
    path: str = "."


@dataclass
class MemoryConfig(StorageConfig):
    kind: str = "memory"
    capacity: int = 100


@register(kind="local")
@dataclass
class LocalStorage:
    config: LocalConfig


@register(kind="memory")
@dataclass
class MemoryStorage:
    config: MemoryConfig


storage = dispatch(StorageConfig, {"kind": "memory", "capacity": "20"})
assert isinstance(storage, MemoryStorage)
assert storage.config.capacity == 20
saved = to_dict(storage.config)
assert saved == {"kind": "memory", "capacity": 20}
assert dispatch(StorageConfig, saved).config == storage.config
```

Keep `@register` above `@dataclass`. A constructor receives one converted config
instance. A function can also be registered; inference reads its first positional
parameter, which must be named `config` and annotated with a concrete config type.

## Registration rules

- `@register()` infers the type and adds an unconditional registration.
- `@register(Field("size") > 0, kind="batch")` combines positional expressions
  with keyword equality matches. All conditions must pass.
- Every keyword is an input field name. `when=` and `config=` are not decorator
  options. Positional arguments after an optional explicit type must be expressions.
- `@register(ConfigType, ...)` overrides inference. Use it for unannotated
  constructors or local forward references that cannot resolve at registration.
- Stack decorators to register one constructor for several config types.
- Class annotations may be inherited. Missing, unresolved, or union config
  annotations fail inference. Define referenced types before registration.
- Registrations are shared within the process. Re-registering the same constructor
  and config type replaces its conditions. A different constructor adds a rule.

## Dispatch semantics

Mapping dispatch loops over registrations for the requested type and its
subclasses. It evaluates rules against raw input before conversion. Keyword
matches require key presence, even when the required value is `None`.

Overlapping registrations are allowed. Zero or multiple matches raise `ValueError`
at dispatch time, before construction. Registration order never breaks ties.
Validation and constructor errors propagate after selection.

`dispatch(config_instance)` uses its exact type without evaluating matching rules
or revalidating fields. Multiple constructors for that type are ambiguous, even
if their mapping rules differ. `dispatch(ConfigType, instance)` checks the
instance type and uses the same instance behavior.

`Field` reads literal top-level keys. Use `&`, `|`, and `~` to compose expressions,
not Python's `and`, `or`, and `not`. Compound expressions evaluate both operands;
do not rely on short-circuit guards.

## Conversion and persistence

- `from_dict(Type, data)` converts values; it does not select implementations.
- Typed dataclass fields, lists, and dictionaries convert recursively, including
  nested dataclasses and dictionary keys. No nested implementation dispatch occurs.
- Plain dataclasses reject undeclared input fields with `TypeError`. Declare all
  matching keys, including `kind`, as regular fields rather than `ClassVar`.
- Pydantic models and Pydantic dataclasses retain their native validation and
  extra-field policies. Set `extra="forbid"` in the appropriate Pydantic config
  if undeclared fields must be rejected.
- `to_dict(config)` serializes declared fields. It does not inject registration
  conditions. Output may contain non-JSON values such as dates or UUIDs.
- Save the config, not the implementation. Import registration modules before
  reloading in another process. Saved values must still satisfy the rules.
- Direct dataclass construction does not invoke Nightjar conversion.

Use `from __future__ import annotations` for Python 3.9 annotations containing
`A | B`. Runtime aliases still need `typing.Union` on Python 3.9. Pydantic models
follow the installed version's annotation support.

## Avoid removed APIs

Do not generate imports of `BaseConfig`, `BaseModule`, `AutoModule`, or
`DispatchRegistry`. Do not use `nightjar.base`, `nightjar.utils`, or
`nightjar.serializers`. There is no automatic `Config.from_dict` method,
class-level `__match__` dispatch, or `to_dict(..., dispatch=False)` option.

For custom conversion, use the public `converter_registry` and its
`register_type` method. See [custom converters](guides/custom-converters.md).

## Verify generated code

Exercise each implementation choice, missing and ambiguous matches, and a
save/reload round trip when persistence matters. Run examples against the project's
installed Pydantic version rather than assuming identical coercion across versions.

When contributing to this repository:

```bash
uv run python -m unittest discover -s tests -p 'test_*.py'
uv run --group docs mkdocs build --strict
```

See the [dispatch guide](guides/dispatch.md), [conversion guide](guides/conversion.md),
and [API reference](reference/configuration.md) for details.
