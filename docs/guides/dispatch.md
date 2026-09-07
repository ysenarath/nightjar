# Dispatch

## Discriminator fields

Declare `dispatch=["kind"]` on a configuration family to select subclasses by
their `kind` attribute, as in the [quickstart](../getting-started.md).
Discriminators declared as `ClassVar` are included when the configuration is
serialized, even though they are not dataclass constructor fields.

## Predicates

For selection rules beyond exact discriminator matching, define `__match__`
using `Field` expressions on a family without a `dispatch` list:

```python
from nightjar import BaseConfig, Field


class JobConfig(BaseConfig):
    pass


class BatchConfig(JobConfig):
    __match__ = Field("kind").str.eq("batch", case=False)
    kind: str = "batch"
    workers: int = 1


config = JobConfig.from_dict({"kind": "BATCH", "workers": "3"})
assert isinstance(config, BatchConfig)
assert config.workers == 3
```

Compose comparisons with `&`, `|`, and `~`. Parenthesize comparisons when
combining them. `Field("key").exists()` checks whether a key is present,
including when its value is `None`. Field names refer to literal top-level keys.

!!! note "Predicate evaluation"
    Compound expressions evaluate both operands. They do not short-circuit like
    Python's `and` and `or`; an existence check does not guard evaluation of the
    other operand.

## Register plain classes

Use `register` when an implementation does not inherit from `BaseModule`.
Its constructor must accept a configuration instance:

```python
from dataclasses import dataclass
from typing import ClassVar
from nightjar import BaseConfig, dispatch, register


class TaskConfig(BaseConfig, dispatch=["kind"]):
    kind: ClassVar[str]


class EchoConfig(TaskConfig):
    kind: ClassVar[str] = "echo"
    message: str = "Hello"


@register(EchoConfig)
@dataclass
class Echo:
    config: EchoConfig


task = dispatch(TaskConfig, {"kind": "echo", "message": "Hi"})
assert isinstance(task, Echo)
assert task.config.message == "Hi"
```

## Selection errors

Configuration selection and implementation selection must each produce one
match. Missing or ambiguous matches raise `ValueError`. Keep predicates mutually
exclusive and register only one implementation for each concrete configuration.
Conversion and constructor errors propagate to the caller.
