import unittest
from dataclasses import dataclass

from nightjar import BaseConfig, Field, dispatch, register


class VehicleConfig(BaseConfig): ...


class CarConfig(VehicleConfig):
    __match__ = Field("type").str.eq("car", case=False) | (
        Field("num_doors") == 4
    )

    type: str = "car"
    num_doors: int = 4


@register(CarConfig)
@dataclass
class Car:
    config: CarConfig


class VanConfig(VehicleConfig):
    __match__ = (
        Field("type").str.eq("van", case=False) & ~Field("num_doors").exists()
    )

    type: str = "van"


class AltVanConfig(VehicleConfig):
    __match__ = Field("type").str.eq("van", case=False) & (
        Field("num_doors").exists()
    )

    type: str = "van"
    num_doors: int = 4


@register(AltVanConfig, VanConfig)
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
