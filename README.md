# Nightjar

[![PyPI version](https://badge.fury.io/py/nightjar.svg)](https://badge.fury.io/py/nightjar)
![PyPI - Downloads](https://img.shields.io/pypi/dm/nightjar)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nightjar)
![GitHub](https://img.shields.io/github/license/ysenarath/nightjar)

A config dispatch library.
Supports dataclasses, Pydantic models, and custom converters.

## Install

```bash
uv add nightjar
```

## Usage

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

The caller supplies `StorageConfig`; `kind` selects the implementation.
`@register` infers each concrete config type from its annotation.

## Compatibility

- Python 3.9+: use `from __future__ import annotations` for `A | B` annotations on 3.9.
- Pydantic v1.10 and v2 are supported without an exact version pin. Conversion
  behavior follows the installed version; uv resolves a compatible release.

Preview the documentation with `uv run --group docs mkdocs serve`.

[Documentation](docs/index.md) ·
[Issues](https://github.com/ysenarath/nightjar/issues) ·
[MIT License](LICENSE)
