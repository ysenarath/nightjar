from typing import ClassVar

from nightjar import AutoModule, BaseConifg, BaseModule


class VehicleConfig(BaseConifg, dispatch=["type"]):
    type: ClassVar[str]


class Vehicle(BaseModule):
    config: VehicleConfig


class AutoVehicle(AutoModule):
    def __new__(cls, config: VehicleConfig) -> Vehicle:
        return super().__new__(cls, config)
