# Getting started

```bash
uv add nightjar
```

## Select a storage implementation

Define a shared config family and register two implementations. The caller
passes the family to `dispatch`; input data determines which implementation
to construct:

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

Both calls use `StorageConfig`. The `kind` value selects a registration, then
Nightjar converts the input into `LocalConfig` or `MemoryConfig` and passes it
to the corresponding constructor. For example, `"20"` becomes an integer.

`@register` infers the concrete config type from each implementation's `config`
annotation. The shared family scopes selection to storage implementations.
Matching keys such as `kind` are regular fields so they survive serialization.

If you already have a concrete configuration, use `dispatch(config)`. This selects
the unique constructor registered for its exact type and preserves the instance:

```python
config = MemoryConfig(capacity=30)
assert dispatch(config).config is config
```

Continue with [dispatch](guides/dispatch.md) for predicates, Pydantic models,
and saving configurations to rebuild implementations later.
