# Nightjar

A config dispatch library.

Register constructors for plain dataclasses or Pydantic models, then select an
implementation from configuration. Start with the [quickstart](getting-started.md).

```bash
uv add nightjar
```

```python
from pydantic import BaseModel
from nightjar import from_dict, to_dict


class Item(BaseModel):
    count: int
    enabled: bool = True


item = from_dict(Item, {"count": "4", "enabled": "false"})
assert to_dict(item) == {"count": 4, "enabled": False}
```

- [Get started](getting-started.md) with typed configuration and object construction.
- [Select implementations](guides/dispatch.md) using discriminator fields or predicates.
- [Convert data](guides/conversion.md) with dataclasses, containers, and Pydantic models.
- [Extend conversion](guides/custom-converters.md) for application-specific types.
- Browse the [API reference](reference/configuration.md), generated from source docstrings.

Nightjar supports Python 3.9+ and Pydantic v1.10 and v2. See
[compatibility](compatibility.md) for annotation syntax and version-dependent behavior.
