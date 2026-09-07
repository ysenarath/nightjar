# Dispatch

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


@register(LocalConfig, kind="local")
@dataclass
class LocalStorage:
    config: LocalConfig


@register(MemoryConfig, kind="memory")
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

Pass a `Field` expression through `when` for rules beyond exact equality:

```python
from dataclasses import dataclass
from nightjar import Field, dispatch, register


@dataclass
class BatchConfig:
    workers: int = 1


@register(BatchConfig, when=Field("kind").str.eq("batch", case=False))
def build_batch(config):
    return config


config = dispatch(BatchConfig, {"kind": "BATCH", "workers": "3"})
assert isinstance(config, BatchConfig)
assert config.workers == 3
```

Constructors can be functions or classes; they receive one converted
configuration argument. Combine keyword matches and `when` to require both.
If `when` is omitted, Nightjar uses the configuration type's `__match__`
expression when present.

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


@register(JobConfig, kind="job")
def build_job(config):
    return config


job = dispatch(JobConfig, {"kind": "job", "workers": "2"})
assert job.workers == 2
```

Model validation and handling of extra input fields follow the installed
Pydantic version and model configuration.

## Registration and errors

`@register(FirstConfig, SecondConfig)` associates one constructor with multiple
configuration types. Registrations are shared within the process. Registering
the same constructor and configuration type again replaces their selection rule.

Mapping dispatch requires exactly one matching registration. Missing or
ambiguous matches raise `ValueError`; validation and constructor errors propagate.
Multiple constructors for the same configuration type can use distinct mapping
rules, but dispatching an instance of that type is ambiguous: instance dispatch
uses the exact type without evaluating rules. `dispatch(ConfigType, instance)`
behaves the same way after checking that the instance belongs to `ConfigType`.

`from_dict` only converts values. It does not select registered implementations
or automatically dispatch nested configurations.
