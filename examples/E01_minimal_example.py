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


dict_cfg = {"type": "car", "num_doors": 2}

vehicle_cfg = VehicleConfig.from_dict(dict_cfg)
car = AutoVehicle(vehicle_cfg)
assert isinstance(car, Car)
assert car.config.num_doors == 2
