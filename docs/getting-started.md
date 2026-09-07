# Getting started

```bash
uv add nightjar
```

## Register an implementation

Define a plain dataclass and register a constructor for it:

```python
from dataclasses import dataclass
from nightjar import dispatch, register, to_dict


@dataclass
class CarConfig:
    kind: str = "car"
    doors: int = 4


@register(CarConfig, kind="car")
@dataclass
class Car:
    config: CarConfig

    def describe(self):
        return f"Car with {self.config.doors} doors"


car = dispatch(CarConfig, {"kind": "car", "doors": "2"})
assert isinstance(car, Car)
assert car.describe() == "Car with 2 doors"
assert to_dict(car.config) == {"kind": "car", "doors": 2}

config = CarConfig(doors=3)
assert dispatch(config).config is config
```

`kind="car"` is a required input match, checked before conversion. Nightjar
converts the data to `CarConfig` and calls `Car(config)`. The decorator preserves
`Car`; no Nightjar base class is needed.

With an existing configuration instance, `dispatch(config)` selects the unique
constructor registered for its exact type. It preserves the instance and does
not recheck predicates or discriminator values.

Continue with [dispatch](guides/dispatch.md) for configuration families,
Pydantic models, and predicates.
