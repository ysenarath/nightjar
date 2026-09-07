# Getting started

Install Nightjar into your project:

```bash
uv add nightjar
```

## Define configuration and an implementation

A direct subclass of `BaseConfig` defines a configuration family. Subclasses of
that family are registered automatically and become dataclasses without needing
the `@dataclass` decorator.

```python
from __future__ import annotations

from typing import ClassVar
from nightjar import AutoModule, BaseConfig, BaseModule, dispatch, to_dict


class VehicleConfig(BaseConfig, dispatch=["kind"]):
    kind: ClassVar[str]


class CarConfig(VehicleConfig):
    kind: ClassVar[str] = "car"
    doors: int = 4


class Car(BaseModule):
    config: CarConfig

    def describe(self):
        return f"Car with {self.config.doors} doors"


car = dispatch(VehicleConfig, {"kind": "car", "doors": "2"})
assert isinstance(car, Car)
assert car.describe() == "Car with 2 doors"
assert to_dict(car.config) == {"kind": "car", "doors": 2}

config = VehicleConfig.from_dict({"kind": "car"})
assert isinstance(AutoModule(config), Car)
```

The `kind` class variable selects the configuration subtype. The `config`
annotation on `Car` registers the implementation. Loading converts field values
before passing the configuration to the implementation constructor.

Use `dispatch` when starting from a dictionary, or `AutoModule` when you already
have a configuration instance. Both require a unique registered implementation.

Continue with [dispatch](guides/dispatch.md) for predicates and registration of
classes that do not inherit from `BaseModule`.
