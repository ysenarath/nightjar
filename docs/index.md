# Nightjar

A config dispatch library.

Register constructors for plain dataclasses or Pydantic models, then select an
implementation from configuration. Start with the [quickstart](getting-started.md).

```bash
uv add nightjar
```

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

local = dispatch(StorageConfig, {"kind": "local", "path": "./data"})
assert isinstance(local, LocalStorage)
```

The same `dispatch(StorageConfig, data)` call builds either implementation,
depending on the input.

- [Get started](getting-started.md) with typed configuration and object construction.
- [Select implementations](guides/dispatch.md) using discriminator fields or predicates.
- [Convert data](guides/conversion.md) with dataclasses, containers, and Pydantic models.
- [Extend conversion](guides/custom-converters.md) for application-specific types.
- Browse the [API reference](reference/configuration.md), generated from source docstrings.

Nightjar supports Python 3.9+ and Pydantic v1.10 and v2. See
[compatibility](compatibility.md) for annotation syntax and version-dependent behavior.
