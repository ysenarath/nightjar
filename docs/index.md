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
class CarConfig:
    doors: int = 4


@register(kind="car")
@dataclass
class Car:
    config: CarConfig


car = dispatch(CarConfig, {"kind": "car", "doors": "2"})
assert car.config.doors == 2
```

- [Get started](getting-started.md) with typed configuration and object construction.
- [Select implementations](guides/dispatch.md) using discriminator fields or predicates.
- [Convert data](guides/conversion.md) with dataclasses, containers, and Pydantic models.
- [Extend conversion](guides/custom-converters.md) for application-specific types.
- Browse the [API reference](reference/configuration.md), generated from source docstrings.

Nightjar supports Python 3.9+ and Pydantic v1.10 and v2. See
[compatibility](compatibility.md) for annotation syntax and version-dependent behavior.
