import unittest
from dataclasses import dataclass
from operator import or_

from nightjar import Field, dispatch, register


@dataclass
class VehicleConfig: ...


@dataclass
class CarConfig(VehicleConfig):
    type: str = "car"
    num_doors: int = 4


@register(
    CarConfig,
    or_(Field("type").str.eq("car", case=False), Field("num_doors") == 4),
)
@dataclass
class Car:
    config: CarConfig


@dataclass
class VanConfig(VehicleConfig):
    type: str = "van"


@register(VanConfig, Field("type").str.eq("van", case=False))
@dataclass
class Van:
    config: VanConfig


@dataclass
class BicycleConfig(VehicleConfig):
    type: str = "bicycle"
    num_doors: int = 0


@register(
    BicycleConfig,
    (Field("type").str.lower() == "bicycle") | (Field("num_doors") == 0),
)
@dataclass
class Bicycle:
    config: BicycleConfig


class TestVehicle(unittest.TestCase):
    def test_car_by_type_case_insensitive(self):
        v = dispatch(VehicleConfig, {"type": "CAR"})
        self.assertIsInstance(v, Car)
        assert isinstance(v, Car)  # for type checkers

    def test_car_by_num_doors(self):
        v = dispatch(VehicleConfig, {"num_doors": 4})
        self.assertIsInstance(v, Car)
        assert isinstance(v, Car)  # for type checkers

    def test_van_by_type(self):
        v = dispatch(VehicleConfig, {"type": "van"})
        self.assertIsInstance(v, Van)
        assert isinstance(v, Van)  # for type checkers

    def test_bicycle_by_type(self):
        v = dispatch(VehicleConfig, {"type": "BICYCLE"})
        self.assertIsInstance(v, Bicycle)
        assert isinstance(v, Bicycle)  # for type checkers

    def test_bicycle_by_num_doors(self):
        v = dispatch(VehicleConfig, {"num_doors": 0})
        self.assertIsInstance(v, Bicycle)
        assert isinstance(v, Bicycle)  # for type checkers


if __name__ == "__main__":
    unittest.main()
