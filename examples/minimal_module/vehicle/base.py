from typing import ClassVar

from nightjar import AutoModule, BaseConfig, BaseModule


class VehicleConfig(BaseConfig, dispatch=["type"]):
    type: ClassVar[str]


class Vehicle(BaseModule):
    config: VehicleConfig


class AutoVehicle(AutoModule):
    def __new__(cls, config: VehicleConfig) -> Vehicle:
        return super().__new__(cls, config)
