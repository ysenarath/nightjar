from .base import AutoVehicle, Vehicle, VehicleConfig  # noqa: TID252
from .car import Car, CarConfig  # noqa: TID252
from .van import Van, VanConfig  # noqa: TID252

# [NOTE] you have to import all the classes that you want to be available

__all__ = [
    "AutoVehicle",
    "Car",
    "CarConfig",
    "Van",
    "VanConfig",
    "Vehicle",
    "VehicleConfig",
]
