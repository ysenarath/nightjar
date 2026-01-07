import unittest
from typing import ClassVar

from nightjar import AutoModule, BaseConfig, BaseModule


class VehicleConfig(BaseConfig, dispatch=["type"]):
    type: ClassVar[str]


class Vehicle(BaseModule):
    config: VehicleConfig


class AutoVehicle(AutoModule):
    pass


class CarConfig(VehicleConfig):
    type: ClassVar[str] = "car"
    num_doors: int = 4


class Car(Vehicle):
    config: CarConfig


class VanConfig(VehicleConfig):
    type: ClassVar[str] = "van"


class Van(Vehicle):
    config: VanConfig


class TestVehicle(unittest.TestCase):
    def test_car_with_custom_doors(self):
        config = {"type": "car", "num_doors": 2}
        vehicle_cfg = VehicleConfig.from_dict(config)
        car = AutoVehicle(vehicle_cfg)
        self.assertIsInstance(car, Car)
        assert isinstance(car, Car)  # for type checkers
        self.assertEqual(car.config.num_doors, 2)


if __name__ == "__main__":
    unittest.main()
