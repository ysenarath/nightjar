# Dispatch

## Registration

`@register(...)` infers the config type from a class's `config` attribute or a
function's first positional parameter named `config`. Use `@register()` when
no conditions are needed. Place `@register` above `@dataclass`.

Pass a type explicitly with `@register(ConfigType, ...)` to override inference
or register a constructor without annotations. Inherited class annotations work;
missing, unresolved, or union annotations raise `TypeError`. Postponed annotations
must resolve in the defining module. For local forward references, pass the type
explicitly.

## Configuration families

Pass a common configuration class to select among its registered subclasses.
Each registration supplies the input values required to select it:

```python
from dataclasses import dataclass
from nightjar import dispatch, register


@dataclass
class StorageConfig:
    pass


@dataclass
class LocalConfig(StorageConfig):
    path: str = "."


@dataclass
class MemoryConfig(StorageConfig):
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
```

Keyword matches use literal top-level keys. Every specified key must exist and
match its value; `kind=None` does not match a missing key. Selection happens on
raw input, before validation. The complete input mapping is passed to conversion.
Plain dataclasses ignore unknown keys, so `kind` need not be a dataclass field.
Declare it as a field if it should appear in serialized output.

## Predicates

Pass positional `Field` expressions for rules beyond exact equality:

```python
from dataclasses import dataclass
from nightjar import Field, dispatch, register


@dataclass
class BatchConfig:
    workers: int = 1


@register(Field("kind").str.eq("batch", case=False))
def build_batch(config: BatchConfig):
    return config


config = dispatch(BatchConfig, {"kind": "BATCH", "workers": "3"})
assert isinstance(config, BatchConfig)
assert config.workers == 3
```

All positional expressions and keyword matches must pass. Every keyword names
an input field, including `when` and `config`:

```python
@register(Field("workers") > 0, when="startup", config="batch")
def start_batch(config: BatchConfig):
    return config


assert dispatch(
    BatchConfig, {"workers": 2, "when": "startup", "config": "batch"}
).workers == 2
```

Keyword matches become presence-and-equality expressions. Dispatch checks
registrations in a loop and requires a unique match.

Compose comparisons with `&`, `|`, and `~`, and parenthesize comparisons.
`Field("key").exists()` checks presence, including a value of `None`.

!!! note "Predicate evaluation"
    Compound expressions evaluate both operands. They do not short-circuit like
    Python's `and` and `or`; an existence check does not guard the other operand.

## Pydantic configurations

Pydantic models work with the same registration API:

```python
from typing import Literal
from pydantic import BaseModel
from nightjar import dispatch, register


class JobConfig(BaseModel):
    kind: Literal["job"] = "job"
    workers: int = 1


@register(kind="job")
def build_job(config: JobConfig):
    return config


job = dispatch(JobConfig, {"kind": "job", "workers": "2"})
assert job.workers == 2
```

Model validation and handling of extra input fields follow the installed
Pydantic version and model configuration.

## Registration and errors

Stack `@register(FirstConfig, ...)` and `@register(SecondConfig, ...)` to
associate one constructor with multiple configuration types. Registrations are
shared within the process; re-registering the same constructor and type replaces
its conditions.

Mapping dispatch requires exactly one matching registration. Missing or
ambiguous matches raise `ValueError`; validation and constructor errors propagate.
Multiple constructors for the same configuration type can use distinct mapping
rules, but dispatching an instance of that type is ambiguous: instance dispatch
uses the exact type without evaluating rules. `dispatch(ConfigType, instance)`
behaves the same way after checking that the instance belongs to `ConfigType`.

`from_dict` only converts values. It does not select registered implementations
or automatically dispatch nested configurations.
