import unittest

from nightjar import AutoModule, BaseConfig, BaseModule, Field


class VehicleConfig(BaseConfig): ...


class Vehicle(BaseModule, AutoModule):
    config: VehicleConfig


class CarConfig(VehicleConfig):
    __match__ = Field("type").str.eq("car", case=False) | (
        Field("num_doors") == 4
    )

    type: str = "car"
    num_doors: int = 4


class Car(Vehicle):
    config: CarConfig


class VanConfig(VehicleConfig):
    __match__ = Field("type").str.eq("van", case=False)

    type: str = "van"


class Van(Vehicle):
    config: VanConfig


class BicycleConfig(VehicleConfig):
    __match__ = (Field("type").str.lower() == "bicycle") | (
        Field("num_doors") == 0
    )

    type: str
    num_doors: int = 0


class TestVehicle(unittest.TestCase):
    def test_car_by_type_case_insensitive(self):
        v = Vehicle({"type": "CAR"})
        self.assertIsInstance(v, Car)
        assert isinstance(v, Car)  # for type checkers

    def test_car_by_num_doors(self):
        v = Vehicle({"num_doors": 4})
        self.assertIsInstance(v, Car)
        assert isinstance(v, Car)  # for type checkers

    def test_van_by_type(self):
        v = Vehicle({"type": "van"})
        self.assertIsInstance(v, Van)
        assert isinstance(v, Van)  # for type checkers


if __name__ == "__main__":
    unittest.main()
