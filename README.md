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
class CarConfig:
    kind: str = "car"
    doors: int = 4


@register(kind="car")
@dataclass
class Car:
    config: CarConfig


car = dispatch(CarConfig, {"kind": "car", "doors": "2"})
assert car.config.doors == 2
```

`@register` infers the config type from the annotation. Use positional `Field`
expressions for more complex matching rules.

## Compatibility

- Python 3.9+: use `from __future__ import annotations` for `A | B` annotations on 3.9.
- Pydantic v1.10 and v2 are supported without an exact version pin. Conversion
  behavior follows the installed version; uv resolves a compatible release.

Preview the documentation with `uv run --group docs mkdocs serve`.

[Documentation](docs/index.md) ·
[Issues](https://github.com/ysenarath/nightjar/issues) ·
[MIT License](LICENSE)
