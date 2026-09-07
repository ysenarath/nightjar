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
```

Keyword matches use literal top-level keys. Every specified key must exist and
match its value; `kind=None` does not match a missing key. Selection happens on
raw input, before validation. The complete input mapping is passed to conversion.
Plain dataclasses reject undeclared input keys with `TypeError`. Declare matching
keys such as `kind` as regular fields so they survive serialization.

## Save and rebuild

Declare every input matching key as a regular config field, including `kind`.
Using the storage classes above, save the config and dispatch it again:

```python
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from nightjar import to_dict


with TemporaryDirectory() as directory:
    path = Path(directory) / "storage.json"
    path.write_text(json.dumps(to_dict(storage.config)), encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))

assert data == {"kind": "memory", "capacity": 20}
restored = dispatch(StorageConfig, data)
assert isinstance(restored, MemoryStorage)
assert restored.config == storage.config
```

In a new process, import the modules containing your registrations before
loading the file. Registrations are not stored in JSON. The saved values must
still satisfy the matching rules; validation that changes a value used by a
predicate can change which registration matches on reload.

This example uses JSON-compatible fields. See [conversion](conversion.md#python-output)
for other Python values.

## Predicates

Pass positional `Field` expressions for rules beyond exact equality:

```python
from dataclasses import dataclass
from nightjar import Field, dispatch, register


@dataclass
class BatchConfig:
    kind: str = "batch"
    when: str = "startup"
    config: str = "batch"
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

### Ambiguity is checked at dispatch time

Registration accepts overlapping rules, including identical rules for different
implementations. It does not check for ambiguity when a class or function is
defined. Each mapping dispatch evaluates the registered rules against its input
and requires exactly one match. Zero or multiple matches raise `ValueError`
before an implementation constructor is called. Registration order does not
break ties.

This example is independent of the storage family above:

```python
from dataclasses import dataclass
from nightjar import dispatch, register


@dataclass
class SharedConfig:
    kind: str
    path: str = "."


@register(kind="local")
@dataclass
class Local:
    config: SharedConfig


@register(kind="remote")
@dataclass
class Remote:
    config: SharedConfig


@register(kind="remote")
@dataclass
class AlternativeRemote:
    config: SharedConfig


# All three registrations succeed. Only the remote input is ambiguous.
assert isinstance(dispatch(SharedConfig, {"kind": "local"}), Local)

try:
    dispatch(SharedConfig, {"kind": "remote"})
except ValueError as error:
    assert "found 2" in str(error)
else:
    raise AssertionError("Expected an ambiguous dispatch")
```

To distinguish both remote implementations, give them additional matching
conditions. Validation and constructor errors propagate after a unique match
has been selected.

### Dispatching existing instances

Multiple constructors for the same configuration type can use distinct mapping
rules, but dispatching an instance of that type is ambiguous: instance dispatch
uses the exact type without evaluating rules. `dispatch(ConfigType, instance)`
behaves the same way after checking that the instance belongs to `ConfigType`.

`from_dict` only converts values. It does not select registered implementations
or automatically dispatch nested configurations.
