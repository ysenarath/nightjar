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
from pydantic import BaseModel
from nightjar import from_dict, to_dict

class Item(BaseModel):
    count: int
    enabled: bool = True

item = from_dict(Item, {"count": "4", "enabled": "false"})
assert to_dict(item) == {"count": 4, "enabled": False}
```

Use `@register(ConfigType, kind="value")` and `dispatch(ConfigType, data)` to
construct implementations from configuration. No Nightjar base classes required.

## Compatibility

- Python 3.9+: use `from __future__ import annotations` for `A | B` annotations on 3.9.
- Pydantic v1.10 and v2 are supported without an exact version pin. Conversion
  behavior follows the installed version; uv resolves a compatible release.
- Import conversion helpers from `nightjar`; `nightjar.serializers` has been removed.

Preview the documentation with `uv run --group docs mkdocs serve`.

[Documentation](docs/index.md) ·
[Issues](https://github.com/ysenarath/nightjar/issues) ·
[MIT License](LICENSE)
