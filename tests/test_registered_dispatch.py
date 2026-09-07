from __future__ import annotations

import unittest
from dataclasses import dataclass

from nightjar import Field, dispatch, register


@dataclass
class VehicleConfig: ...


@dataclass
class CarConfig(VehicleConfig):
    type: str = "car"
    num_doors: int = 4


@register(
    CarConfig,
    Field("type").str.eq("car", case=False) | (Field("num_doors") == 4),
)
@dataclass
class Car:
    config: CarConfig


@dataclass
class VanConfig(VehicleConfig):
    type: str = "van"


@dataclass
class AltVanConfig(VehicleConfig):
    type: str = "van"
    num_doors: int = 4


@register(
    AltVanConfig,
    Field("type").str.eq("van", case=False) & Field("num_doors").exists(),
)
@register(
    VanConfig,
    Field("type").str.eq("van", case=False) & ~Field("num_doors").exists(),
)
@dataclass
class Van:
    config: VanConfig | AltVanConfig


class TestVehicle(unittest.TestCase):
    def test_default_car(self):
        v = dispatch(VehicleConfig, {"type": "CAR"})
        self.assertIsInstance(v, Car)
        assert isinstance(v, Car)  # for type checkers

    def test_car(self):
        v = dispatch(VehicleConfig, {"num_doors": 4})
        self.assertIsInstance(v, Car)
        assert isinstance(v, Car)  # for type checkers

    def test_van(self):
        v = dispatch(VehicleConfig, {"type": "van"})
        self.assertIsInstance(v, Van)
        assert isinstance(v, Van)  # for type checkers
        self.assertIsInstance(v.config, VanConfig)

    def test_alt_van(self):
        v = dispatch(VehicleConfig, {"type": "van", "num_doors": 5})
        self.assertIsInstance(v, Van)
        assert isinstance(v, Van)  # for type checkers
        self.assertIsInstance(v.config, AltVanConfig)
        assert isinstance(v.config, AltVanConfig)  # for type checkers
        self.assertEqual(v.config.num_doors, 5)


if __name__ == "__main__":
    unittest.main()
