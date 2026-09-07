# Compatibility

## Python 3.9 and later

Nightjar supports Python 3.9+. On Python 3.9, postpone annotation evaluation to
use `A | B` in annotations that Nightjar resolves:

```python
from __future__ import annotations

from dataclasses import dataclass
from nightjar import from_dict


@dataclass
class Options:
    retries: int | None = None


assert from_dict(Options, {"retries": "3"}).retries == 3
```

The future import affects annotations only. A runtime alias such as
`Alias = int | str` still requires Python 3.10+. Use `typing.Union[int, str]`
for runtime aliases on Python 3.9. Pydantic models use Pydantic's own annotation
handling; Nightjar's resolver does not change what that version accepts.

## Pydantic versions

Nightjar supports Pydantic v1.10 and v2 without an exact dependency pin. It uses
the installed version's APIs. Installing Nightjar through uv resolves a
compatible Pydantic release if necessary; Nightjar does not install dependencies
at runtime. Support for future major versions is not implied.

Validation, coercion, and model serialization follow the installed version.
Applications that need identical validation behavior across environments should
manage their Pydantic version in their own dependency constraints and lockfile.

## Imports

Import `from_dict`, `to_dict`, and `converter_registry` from `nightjar`.
The former `nightjar.serializers` and `nightjar.utils` modules have been removed.
Annotation helpers live in `nightjar.annotations`; most applications can use the
top-level conversion API without calling them directly.
