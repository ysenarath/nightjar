import unittest
from dataclasses import dataclass
from typing import ClassVar

from nightjar import dispatch, register


@dataclass
class VehicleConfig:
    type: ClassVar[str]


@dataclass
class CarConfig(VehicleConfig):
    type: ClassVar[str] = "car"
    num_doors: int = 4


@register(CarConfig, type="car")
@dataclass
class Car:
    config: CarConfig


@dataclass
class VanConfig(VehicleConfig):
    type: ClassVar[str] = "van"


@register(VanConfig, type="van")
@dataclass
class Van:
    config: VanConfig


class TestVehicle(unittest.TestCase):
    def test_car_with_custom_doors(self):
        config = {"type": "car", "num_doors": 2}
        car = dispatch(VehicleConfig, config)
        self.assertIsInstance(car, Car)
        assert isinstance(car, Car)  # for type checkers
        self.assertEqual(car.config.num_doors, 2)


if __name__ == "__main__":
    unittest.main()
