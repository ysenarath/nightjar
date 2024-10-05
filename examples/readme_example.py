from typing import ClassVar

from nightjar import AutoModule, BaseConifg, BaseModule


class VehicleConfig(BaseConifg, dispatch=["type"]):
    type: ClassVar[str]


class Vehicle(BaseModule):
    config: VehicleConfig


class AutoVehicle(AutoModule):
    def __new__(cls, config: VehicleConfig) -> Vehicle:
        return super().__new__(cls, config)


class CarConfig(VehicleConfig):
    type: ClassVar[str] = "car"


class Car(Vehicle):
    config: CarConfig


class VanConfig(VehicleConfig):
    type: ClassVar[str] = "van"


class Van(Vehicle):
    config: VanConfig


# use from_dict method to create a configuration object from a dictionary this will automatically create the correct jar config.
config = VehicleConfig.from_dict({"type": "car"})
# Now you can create a car object using the configuration object with Auto* object
car = AutoVehicle(config)
# Now you can access the config object
assert car.config.type == "car", f"expected 'car', got '{car.config.type}'"
