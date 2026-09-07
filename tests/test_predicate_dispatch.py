import unittest
from dataclasses import dataclass
from operator import or_

from nightjar import Field, dispatch, register


@dataclass
class VehicleConfig: ...


@dataclass
class CarConfig(VehicleConfig):
    __match__ = or_(
        Field("type").str.eq("car", case=False),
        Field("num_doors") == 4,
    )

    type: str = "car"
    num_doors: int = 4


@register(CarConfig, when=CarConfig.__match__)
@dataclass
class Car:
    config: CarConfig


@dataclass
class VanConfig(VehicleConfig):
    __match__ = Field("type").str.eq("van", case=False)

    type: str = "van"


@register(VanConfig, when=VanConfig.__match__)
@dataclass
class Van:
    config: VanConfig


@dataclass
class BicycleConfig(VehicleConfig):
    # fmt: off
    __match__ = (
        (Field("type").str.lower() == "bicycle")
        | (Field("num_doors") == 0)
    )
    # fmt: on

    type: str = "bicycle"
    num_doors: int = 0


@register(BicycleConfig, when=BicycleConfig.__match__)
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
